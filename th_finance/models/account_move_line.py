# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date, timedelta


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    th_contra_account_id = fields.Many2one('account.account',
                                           string='Tài khoản đối ứng')
    th_analytic_account_id = fields.Many2one('account.analytic.account',
                                             string='Bộ phận chịu chi phí')
