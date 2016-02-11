# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (c) 2012 OpenERP S.A. <http://openerp.com>
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
import openerp
from openerp import models, api, SUPERUSER_ID


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def create(self, vals):
        if self.env.context.get('portal'):
            partner_id = self.env.user.partner_id.id
            salesperson = self.sudo().find_salesperson(partner_id)
            vals['partner_id'] = partner_id
            vals['user_id'] = salesperson.id
            obj = super(SaleOrder, self.sudo(salesperson)).create(vals)
            obj.sudo(salesperson).message_subscribe([partner_id])
            return obj
        return super(SaleOrder, self).create(vals)


    @api.model
    def find_salesperson(self, partner_id):
        orders = self.search([('partner_id', '=', partner_id)])
        if orders:
            return orders[0].user_id
        users = self.search([('id', '!=', SUPERUSER_ID)])
        if users:
            return users[0]
        return self.env['res.users'].browse(SUPERUSER_ID)

    @api.multi
    def action_button_confirm(self):
        if self.env.context.get('portal'):
            for obj in self:
                res = super(SaleOrder, obj.sudo(obj.user_id)).action_button_confirm()
            return res
        return super(SaleOrder, self).action_button_confirm()

    def _get_partner_if_portal(self, cr, uid, context=None):
        context = context or {}
        if context.get('portal', False):
            return self.pool.get('res.users').browse(cr, uid, uid).partner_id.id

    _defaults = {
        'partner_id': _get_partner_if_portal
    }

   
