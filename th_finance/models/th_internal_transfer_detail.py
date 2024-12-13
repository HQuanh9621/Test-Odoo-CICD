# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError


class ThInternalTransferDetail(models.Model):
    _name = 'th.internal.transfer.detail'
    _description = 'Hạch toán chuyển quỹ nội bộ'

    th_internal_transfer_id = fields.Many2one('th.internal.transfer',
                                              required=True,
                                              string='Chuyển quỹ nội bộ',
                                              ondelete='cascade')
    th_description = fields.Text(string='Diễn giải')
    th_journal_id = fields.Many2one('account.journal',
                                    string='Ngân hàng/Quỹ đi')
    th_journal_dest_id = fields.Many2one('account.journal',
                                         string='Ngân hàng/Quỹ đến')
    th_debit_account_id = fields.Many2one('account.account',
                                          string='Tài khoản nợ')
    th_credit_account_id = fields.Many2one('account.account',
                                           string='Tài khoản có')
    th_amount_currency = fields.Float(string='Giá trị',
                                      digits=(16, 0))
    th_amount = fields.Float(string='Giá trị quy đổi',
                             compute='_compute_th_amount',
                             digits=(16, 0))
    th_company_id = fields.Many2one('res.company',
                                    required=True,
                                    default=lambda self: self.env.company.id,
                                    string='Công ty')

    @api.onchange('th_internal_transfer_id')
    def _onchange_th_description(self):
        for record in self:
            if record.th_description is False:
                record.th_description = record.th_internal_transfer_id.th_description

    @api.constrains("th_amount_currency", "th_amount")
    def check_valid_amount(self):
        for record in self:
            if record.th_amount_currency <= 0 or record.th_amount <= 0:
                raise UserError("Vui lòng nhập giá trị và giá trị quy đổi hợp lệ!")

    @api.onchange('th_amount_currency')
    def _onchange_th_amount(self):
        for record in self:
            record.th_amount = record.th_amount_currency * record.th_internal_transfer_id.th_rate

    @api.depends('th_internal_transfer_id.th_rate')
    def _compute_th_amount(self):
        for record in self:
            record.th_amount = record.th_amount_currency * record.th_internal_transfer_id.th_rate

    @api.onchange('th_journal_id')
    def _onchange_th_credit_account_id(self):
        for record in self:
            for rec in record.th_journal_id:
                record.th_credit_account_id = rec.default_account_id
            if not record.th_journal_id:
                record.th_credit_account_id = None

    @api.onchange('th_journal_dest_id')
    def _onchange_th_debit_account_id(self):
        for record in self:
            for rec in record.th_journal_dest_id:
                record.th_debit_account_id = rec.default_account_id
            if not record.th_journal_dest_id:
                record.th_debit_account_id = None
