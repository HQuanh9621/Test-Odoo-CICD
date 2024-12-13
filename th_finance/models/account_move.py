# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = 'account.move'

    th_internal_transfer_id = fields.Many2one('th.internal.transfer',
                                              string='Chuyển quỹ nội bộ')

    def button_draft(self):
        for record in self:
            if record.env.company.fiscalyear_lock_date and record.date <= record.env.company.fiscalyear_lock_date:
                raise UserError(
                    'Đã khoá kỳ kế toán từ ngày %s , bạn không thể đưa về dự thảo bút toán trước ngày khoá.',
                    record.env.company.fiscalyear_lock_date.strftime("%d/%m/%Y"))
        res = super().button_draft()
        for record in self:
            if (record.th_account_payment_id != None and record.th_account_payment_id.th_state == 'posted') or (
                    record.th_internal_transfer_id != None and record.th_internal_transfer_id.th_state == 'posted'):
                raise UserError(('Bạn không thể đưa về dự thảo bút toán của phiếu: %s') % record.ref)
        self.line_ids.filtered(lambda
                                   line: line.sale_line_ids.is_downpayment and not line.sale_line_ids.display_type).sale_line_ids._compute_name()
        return res

    # Ghi dè hàm của account move để cho phép xóa sổ bút toán trước
    @api.ondelete(at_uninstall=False)
    def _unlink_forbid_parts_of_chain(self):
        return True
