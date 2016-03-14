# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010, 2013, 2014 Tiny SPRL (<http://tiny.be>).
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

from openerp.models import Model
from openerp import api


class account_invoice(Model):
    _name = 'account.invoice'
    _inherit = 'account.invoice'

    @api.multi
    def generate_supplier_invoices(self):
        for invoice in self:
            company_id = invoice.company_id
            journal_id = self.get_purchase_journal(company_id.id)
            vals = {
                'type': 'in_invoice',
                'state': 'draft',
                'journal_id': journal_id,
                'date_invoice': invoice.date_invoice,
                'period_id': invoice.period_id.id,
                'user_id': invoice.user_id.id,
                'company_id': company_id.id,
                'origin': invoice.origin,
                'comment': 'Generated from customer invoice ' + invoice.origin
            }
            lines_by_supplier = self.group_by_supplier(invoice)
