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
from openerp.exceptions import except_orm


class account_invoice(Model):
    _name = 'account.invoice'
    _inherit = 'account.invoice'

    def create(self, cr, uid, vals, context=None):
        if not vals.get('date_invoice', False):
            order = self.get_related_sale_order(cr, uid,
                                                vals.get('origin', False),
                                                context)
            vals['date_invoice'] = order and order.date_order or False
        inv_id = super(account_invoice, self).create(cr, uid, vals, context)
        if vals.get('type', False) == 'out_invoice':
            self.generate_supplier_invoices(cr, uid, inv_id, context)
        return inv_id

    def get_other_invoices(self, cr, uid, ids, context=None):
        origin = self.read(cr, uid, ids, ['origin'], context)[0]['origin']
        other_invoices = self.search(cr, uid, [('origin', '=', origin),
                                               ('id', 'not in', ids)],
                                     context=context)
        return other_invoices

    def get_related_sale_order(self, cr, uid, origin, context=None):
        order_obj = self.pool.get('sale.order')
        order = order_obj.search(cr, uid, [('name', '=', origin)],
                                 context=context)
        return order and order_obj.browse(cr, uid, order[0], context) or False

    def get_purchase_journal(self, cr, uid, company_id, context=None):
        journal = self.pool.get('account.journal')
        jids = journal.search(cr, uid, [('type', '=', 'purchase'),
                                        ('company_id', '=', company_id)],
                              context=context)
        return jids and jids[0] or False

    def update_lines_by_supplier(self, lines_by_supplier, supplier, d):
        try:
            lines_by_supplier[supplier].append(d)
        except KeyError:
            lines_by_supplier[supplier] = [d]
        return lines_by_supplier

    def group_by_supplier(self, cr, uid, invoice, context):
        sol_obj = self.pool.get('sale.order.line')
        sc_obj = self.pool.get('sale.context')
        lines_by_supplier = {}
        for line in invoice.invoice_line:
            to_search = [('order_id.name', '=', line.origin),
                         ('product_id', '=', line.product_id.id)]
            sol_ids = sol_obj.search(cr, uid, to_search, context=context)
            if sol_ids:
                if len(sol_ids) > 1:
                    cr.execute('select order_line_id from \
                                sale_order_line_invoice_rel where \
                                invoice_id = %s', (line.id,))
                    sol_ids = cr.fetchall()[0]
                order_line = sol_obj.browse(cr, uid, sol_ids[0], context)
                try:
                    supplier = sc_obj.get_supplier(order_line)
                    data = {'invoice_line': line, 'sale_line': order_line}
                    self.update_lines_by_supplier(lines_by_supplier, supplier, data)
                except except_orm, excep:
                    if order_line.category and order_line.category.lower() == 'package':
                        for line in order_line.sale_order_line_package_line_id:
                            if line.sale_order_line_package_line_conf_id:
                                data = {'invoice_line': line, 'sale_line': line.sale_order_line_package_line_conf_id}
                                self.update_lines_by_supplier(lines_by_supplier, line.supplier_id, data)
                            else:
                                raise excep
                    else:
                        raise excep

        return lines_by_supplier

    def generate_supplier_invoices(self, cr, uid, inv_id, context=None):
        invoice = self.browse(cr, uid, inv_id, context)
        company_id = invoice.company_id
        journal_id = self.get_purchase_journal(cr, uid, company_id.id, context)
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

        lines_by_supplier = self.group_by_supplier(cr, uid, invoice, context)
        for s, lines in lines_by_supplier.items():
            currency_id = lines[0]['sale_line'].currency_cost_id.id
            data = vals.copy()
            data.update({
                'partner_id': s.id,
                'account_id': s.property_account_payable.id,
                'currency_id': currency_id,
                'invoice_line': []
            })
            for l in lines:
                sl = l['sale_line']
                il = l['invoice_line']
                cost_price = self.get_cost_price(cr, uid, sl, currency_id,
                                                 context)

                line_vals = {
                    'name': il.product_id.name,
                    'origin': il.invoice_id.number,
                    'product_id': il.product_id.id,
                    'account_id': il.product_id.categ_id.property_account_expense_categ.id,
                    'quantity': il.quantity,
                    'discount': il.discount,
                    'price_unit': cost_price
                }
                data['invoice_line'].append((0, 0, line_vals))
            inv_id = self.create(cr, uid, data, context)

    def get_cost_price(self, cr, uid, line, currency_id, context=None):
        price = line.price_unit_cost
        order_currency_id = line.order_id.pricelist_id.currency_id.id
        if order_currency_id != currency_id:
            currency_obj = self.pool.get('res.currency')
            price = currency_obj.compute(cr, uid, order_currency_id,
                                         currency_id, price, round=False,
                                         context=context)
        return price

    def _check_price_unit(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)
        if obj.state != 'draft':
            for invoice_line in obj.invoice_line:
                if invoice_line.price_unit <= 0.0:
                    return False
        return True

    _constraints = [
        (_check_price_unit, 'Price unit must be over 0.', ['state']),
    ]
