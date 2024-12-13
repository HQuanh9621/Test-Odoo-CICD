# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import date
from odoo.exceptions import UserError, ValidationError, except_orm


class ThInternalTransfer(models.Model):
    _name = 'th.internal.transfer'
    _description = 'Chuyển quỹ nội bộ'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'th_accounting_date desc'
    _sql_constraints = [
        ('unique_name', 'unique(name)', 'Tên phiếu vừa tạo đã bị trùng, vui lòng đổi tên khác!')
    ]

    name = fields.Char(string='Số chứng từ',
                       default='Mới',
                       copy=False,
                       required=True)
    th_accounting_date = fields.Date(string='Ngày hạch toán',
                                     required=True,
                                     default=date.today(),
                                     tracking=True)
    th_document_date = fields.Date(string='Ngày chứng từ',
                                   required=True,
                                   default=date.today(),
                                   tracking=True)
    th_description = fields.Text(string='Mô tả',
                                 required=True,
                                 tracking=True)
    th_currency_id = fields.Many2one('res.currency',
                                     required=True,
                                     string='Tiền tệ',
                                     default=lambda self: self.env.company.currency_id,
                                     tracking=True)
    th_rate = fields.Float(string='Tỉ giá',
                           required=True)
    th_amount_total = fields.Float(string='Tổng giá trị',
                                   compute='_compute_th_amount_total')
    th_state = fields.Selection([('draft', 'Nháp'),
                                 ('posted', 'Đã vào sổ')],
                                string='Trạng thái',
                                default='draft',
                                required=True,
                                tracking=True)
    th_company_id = fields.Many2one('res.company',
                                    required=True,
                                    default=lambda self: self.env.company.id,
                                    string='Công ty')
    th_internal_transfer_detail_ids = fields.One2many('th.internal.transfer.detail',
                                                      'th_internal_transfer_id',
                                                      string='Hạch toán chuyển quỹ nội bộ')
    th_move_ids = fields.One2many('account.move',
                                  'th_internal_transfer_id',
                                  string='Bút toán')
    th_move_count = fields.Integer(string='Đếm bút toán',
                                   compute='_get_th_move_ids')
    th_currency_company_id = fields.Many2one('res.currency',
                                             default=23,
                                             readonly=True)
    th_check_company_currency = fields.Boolean()
    active = fields.Boolean(default=True)

    # Tự sinh mã phiếu khi lưu
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('thits') or 'Mới'
        type = 'CQNB'
        vals['name'] = f'{type}{vals["name"]}'
        res = super(ThInternalTransfer, self).create(vals)
        return res

    # Logic khi thay đổi loại tiền tệ
    @api.onchange('th_currency_id')
    def _onchange_th_rate(self):
        for record in self:
            record.th_internal_transfer_detail_ids = False
            if record.th_currency_id:
                for rate in record.th_currency_id:
                    record.th_rate = rate.rate
            else:
                record.th_rate = 0
            if record.th_currency_id == record.th_company_id.currency_id:
                record.th_check_company_currency = True
            else:
                record.th_check_company_currency = False

    # Ngăn xoá phiếu khi đã vào sổ
    def unlink(self):
        for record in self:
            if record.th_state == 'posted':
                raise UserError(
                    'Không thế xóa phiếu ở trạng thái Đã vào sổ. Vui lòng đưa phiếu về trạng thái Nháp để thực hiện xóa phiếu!')
            return super().unlink()

    # Tạo chi tiết bút toán
    def prepare_data_account_move_line(self, line):
        new_line = []
        new_line.append((0, 0, {
            'name': line.th_description,
            'date': line.th_internal_transfer_id.th_accounting_date,
            'account_id': line.th_debit_account_id.id,
            'debit': line.th_amount,
            'currency_id': line.th_internal_transfer_id.th_currency_id.id,
            'th_contra_account_id': line.th_credit_account_id.id,
            'amount_currency': line.th_amount_currency,
            'tax_ids': [],
        }))
        new_line.append((0, 0, {
            'name': line.th_description,
            'date': line.th_internal_transfer_id.th_accounting_date,
            'account_id': line.th_credit_account_id.id,
            'credit': line.th_amount,
            'currency_id': line.th_internal_transfer_id.th_currency_id.id,
            'th_contra_account_id': line.th_debit_account_id.id,
            'amount_currency': -line.th_amount_currency,
            'tax_ids': [],
        }))
        return new_line

    # Đếm số lượng bút toán
    @api.depends('th_move_ids')
    def _get_th_move_ids(self):
        for record in self:
            record.th_move_count = len(record.th_move_ids)

    # Nút vào sổ
    def action_post(self):
        self.ensure_one()
        if self.th_state not in ('draft'):
            return
        for move in self:
            # Check khóa kỳ kế toán
            if move.th_company_id.fiscalyear_lock_date:
                if move.th_accounting_date <= move.th_company_id.fiscalyear_lock_date:
                    raise UserError(
                        f'Đã khoá kỳ kế toán từ ngày {move.th_company_id.fiscalyear_lock_date.strftime("%d/%m/%Y")}, bạn không thể vào vào sổ bút toán trước ngày khoá!')
            if not move.th_internal_transfer_detail_ids:
                raise UserError('Vui lòng bổ sung thêm hạch toán để thực hiện vào sổ phiếu!')
            for line in move.th_internal_transfer_detail_ids:
                account_move_line = self.prepare_data_account_move_line(line)
                account_move = self.env['account.move']
                move_vals = {
                    'ref': self.name,
                    'date': self.th_accounting_date,
                    'line_ids': account_move_line,
                    'th_internal_transfer_id': self.id,
                    'currency_id': self.th_currency_id.id,
                    'invoice_date': self.th_document_date,
                }
                new_move = account_move.create(move_vals)
                new_move.line_ids[0].write({'journal_id': line.th_journal_dest_id})
                new_move.line_ids[1].write({'journal_id': line.th_journal_id})
                new_move.action_post()
            self.write({'th_state': 'posted'})
            return True

    # Nút quay lại
    def action_draft(self):
        self.ensure_one()
        if self.th_state not in ('posted'):
            return
        else:
            if self.th_company_id.fiscalyear_lock_date:
                if self.th_accounting_date <= self.th_company_id.fiscalyear_lock_date:
                    raise UserError(
                        f'Đã khoá kỳ kế toán từ ngày {self.th_company_id.fiscalyear_lock_date.strftime("%d/%m/%Y")}, bạn không thể đưa về dự thảo bút toán trước ngày khoá!')
            self.write({'th_state': 'draft'})
            self.th_move_ids.button_draft()
            self.th_move_ids.unlink()
            return True

    # Nút chuyển sang giao diện bút toán
    def action_view_account_move(self):
        view_form_id = self.env.ref('account.view_move_form').id
        if self.th_move_count == 1:
            return {
                'name': 'Bút toán',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.move',
                'view_id': view_form_id,
                'res_id': self.th_move_ids.id,
                'target': 'self',
            }
        else:
            view_tree_id = self.env.ref('account.view_move_tree').id
            return {
                'name': 'Bút toán',
                'type': 'ir.actions.act_window',
                'view_type': 'tree',
                'view_mode': 'tree,form',
                'res_model': 'account.move',
                'view_id': False,
                'view_ids': [(view_tree_id, 'tree'), (view_form_id, 'form')],
                'domain': [('id', 'in', self.th_move_ids.ids)],
                'target': 'self',
            }

    @api.depends('th_internal_transfer_detail_ids.th_amount')
    def _compute_th_amount_total(self):
        for record in self:
            total = 0
            for value in record.th_internal_transfer_detail_ids:
                total += value.th_amount
            record.th_amount_total = total
