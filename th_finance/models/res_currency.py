from odoo import fields, models, api, _
from odoo.exceptions import UserError


class CurrencyRate(models.Model):
    _inherit = 'res.currency.rate'

    def _get_latest_rate(self):
        for record in self:
            # Make sure 'name' is defined when creating a new rate.
            if not record.name:
                raise UserError("Ngày tỷ giá hiện tại đang trống.\nVui lòng đặt ngày.")
            return record.currency_id.rate_ids.sudo().filtered(lambda x: (
                    x.rate
                    and x.company_id == (record.company_id or self.env.company)
                    and x.name < (record.name or fields.Date.today())
            )).sorted('name')[-1:]

    @api.onchange('inverse_company_rate')
    def _inverse_inverse_company_rate(self):
        for currency_rate in self:
            if currency_rate.inverse_company_rate:
                currency_rate.company_rate = 1.0 / currency_rate.inverse_company_rate

    @api.depends('company_rate')
    def _compute_inverse_company_rate(self):
        for currency_rate in self:
            if currency_rate.company_rate:
                currency_rate.inverse_company_rate = 1.0 / currency_rate.company_rate
            else:
                currency_rate.inverse_company_rate = 0
