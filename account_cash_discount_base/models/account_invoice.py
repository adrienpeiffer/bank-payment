# -*- coding: utf-8 -*-
#
##############################################################################
#
#    Authors: Adrien Peiffer
#    Copyright (c) 2014 Acsone SA/NV (http://www.acsone.eu)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api, exceptions, _
from datetime import datetime, timedelta
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    discount_percent = fields.Float(string='Discount Percent',
                                    readonly=True,
                                    states={'draft': [('readonly', False)]})
    discount_amount = fields.Float(string='Amount Discount included',
                                   readonly=True,
                                   states={'draft': [('readonly', False)]})
    discount_delay = fields.Integer(string='Discount Delay (days)',
                                    readonly=True,
                                    states={'draft': [('readonly', False)]})
    discount_due_date = fields.Date(string='Discount Due Date',
                                    readonly=True,
                                    states={'draft': [('readonly', False)]})

    @api.v8
    def _compute_discount_amount(self):
        discount = self.amount_untaxed * (0.0 + self.discount_percent/100)
        return (self.amount_total - discount)

    @api.v8
    def _compute_discount_due_date(self):
        if self.date_invoice:
            date_invoice = datetime.strptime(self.date_invoice,
                                             DEFAULT_SERVER_DATE_FORMAT)
        else:
            date_invoice = datetime.now()
        due_date = date_invoice + timedelta(days=self.discount_delay)
        discount_due_date = due_date.date()
        return discount_due_date

    @api.v8
    def compute_discount_amount(self):
        if (self.type in ['in_invoice', 'out_invoice'] and
                self.discount_percent != 0.0):
            self.discount_amount = self._compute_discount_amount()

    @api.v8
    def compute_discount_due_date(self):
        if self.discount_delay != 0 and (self.type != 'in_invoice' or
                                         self.discount_delay != 0):
            self.discount_due_date = self._compute_discount_due_date()

    @api.multi
    def button_reset_taxes(self):
        res = super(account_invoice, self).button_reset_taxes()
        for invoice in self:
            invoice.compute_discount_amount()
        return res

    @api.multi
    def action_move_create(self):
        super(account_invoice, self).action_move_create()
        for inv in self:
            inv.compute_discount_amount()
            if not inv.discount_due_date and \
                    inv.discount_amount and inv.discount_amount != 0.0:
                raise exceptions.Warning(_('Warning !\n You have to define '
                                           'a discount due date'))
        return True

    @api.multi
    def action_date_assign(self):
        super(account_invoice, self).action_date_assign()
        for inv in self:
            inv.compute_discount_due_date()
        return True
