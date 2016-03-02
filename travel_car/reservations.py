# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010, 2014 Tiny SPRL (<http://tiny.be>).
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

from openerp import fields, api
from openerp.models import Model
from openerp.tools.translate import _


# TODO: Optimizar esto con sql
class cars_reservations(Model):
    _name = "cars.reservations"
    _description = "Cars Reservations"

    sale_order_line_id = fields.Many2one('sale.order.line', _('Sale Order Line'), readonly=True)
    name = fields.Char(_('Name'), readonly=True)
    start_date = fields.Date(_('Start Date'), readonly=True)
    end_date = fields.Date(_('End Date'), readonly=True)
    customer = fields.Char(_('Customer'), readonly=True)
    adults = fields.Integer(_('Adults'), readonly=True)
    children = fields.Integer(_('Children'), readonly=True)
    price = fields.Float(_('Price'), readonly=True)
    original = fields.Boolean(_('Original'), default=True, readonly=True)
    supplier = fields.Char(_('Supplier'), readonly=True)
    state = fields.Selection(
        [('cancel', 'Cancelled'), ('draft', 'Draft'), ('confirmed', 'Confirmed'), ('exception', 'Exception'),
         ('done', 'Done')],
        _('Status'), readonly=True, copy=False)

    _order = 'start_date asc'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        if view_type == 'tree':
            self.env.cr.execute(
                'DELETE FROM cars_reservations WHERE id IN ( SELECT id FROM cars_reservations)')
            sol = self.env['sale.order.line']
            for line in sol.search([]):
                if line.category.lower() == 'car':
                    base_dict = {
                        'sale_order_line_id': line.id,
                        'name': line.product_id.name_template,
                        'start_date': line.order_start_date,
                        'end_date': line.end_date,
                        'adults': line.adults,
                        'children': line.children,
                        'vehicle': line.transfer_1_vehicle_type_id.name,
                        'guide': line.transfer_2_guide_id.name,
                        'confort': line.transfer_3_confort_id.name,
                        'supplier': line.supplier_id.name,
                        'price': line.price_unit,
                        'customer': line.customer_id.name,
                        'state': line.state
                    }
                    self.create(base_dict)
                elif line.category.lower() == 'package' and not line.supplier_id:
                    for package_line in line.sale_order_line_package_line_id:
                        if package_line.category_id.name.lower() == 'car':
                            base_dict = {
                                'sale_order_line_id': line.id,
                                'name': package_line.product_id.name_template,
                                'supplier': package_line.supplier_id.name,
                                'price': line.price_unit,
                                'customer': line.customer_id.name,
                                'original': False,

                            }
                            if package_line.sale_order_line_package_line_conf_id:
                                tmp = package_line.sale_order_line_package_line_conf_id
                                vals = {
                                    'start_date': tmp.start_date,
                                    'end_date': tmp.end_date,
                                    'adults': tmp.adults,
                                    'vehicle': tmp.transfer_1_vehicle_type_id.name,
                                    'guide': tmp.transfer_2_guide_id.name,
                                    'confort': tmp.transfer_3_confort_id.name,
                                    'children': tmp.children
                                }
                                base_dict.update(vals)
                            self.create(base_dict)
        return super(cars_reservations, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                              toolbar=toolbar,
                                                              submenu=submenu)

    @api.multi
    def to_confirm(self):
        obj = self[0]
        obj.write({'state': 'confirmed'})
        return obj.sale_order_line_id.to_confirm()

    @api.multi
    def to_cancel(self):
        obj = self[0]
        obj.write({'state': 'cancel'})
        return obj.sale_order_line_id.to_cancel()

    @api.multi
    def print_voucher(self):
        obj = self[0]
        return obj.sale_order_line_id.print_voucher()

    @api.multi
    def go_to_order(self):
        obj = self[0]
        return obj.sale_order_line_id.go_to_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
