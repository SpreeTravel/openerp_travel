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

import time
import simplejson
import openerp
import datetime as dt
from lxml import etree
from openerp import fields, api, exceptions
from openerp.models import Model
from openerp.exceptions import except_orm
from openerp.tools.translate import _


class sale_order(Model):
    _name = 'sale.order'
    _inherit = 'sale.order'

    order_destination_id = fields.Many2one('destination', 'Country', required=True)


class sale_context(Model):
    _name = 'sale.context'
    _inherit = 'sale.context'

    def _build_attr(self, cr, uid, field):
        category = field.split('_')[0].capitalize()
        category_obj = self.pool.get('product.category')
        category_id = category_obj.search(cr, uid, [('name', '=', category)])
        return {'invisible': [('category_id', '!=', category_id[0])]}

    def _build_ctx(self, base, fields):
        body = ''
        for f in fields:
            body += ", '" + f + "': " + f
        first, last = base.split("'end_date': end_date")
        return first + "'end_date': end_date" + body + last

    def _update_ctx(self, ctx, ap):
        ap = ap.replace('{', '')
        ap = ap.replace('}', '')
        first, last = ctx.split("'end_date': end_date")
        return first + "'end_date': end_date," + ap + last

    def get_context_fields(self, cr, uid, context=None):
        context_fields = {}
        categ = self.pool.get('product.category')
        categ_ids = categ.search(cr, uid, [('type', '=', 'normal')],
                                 context=context)
        categs = [c['name'] for c in categ.read(cr, uid, categ_ids, ['name'])]
        for f, v in self.fields_get(cr, uid).items():
            if f.split('_')[0].capitalize() in categs:
                context_fields[f] = v
        return context_fields

    def update_view_with_context_fields(self, cr, uid, res, context=None, flag=True):
        new_fields = self.get_context_fields(cr, uid, context)
        res['fields'].update(new_fields)
        # new_fields['api_model_id'] = res['fields']['api_model_id']
        # new_fields['destination_id'] = res['fields']['destination_id']
        doc = etree.XML(res['arch'])
        field_names = ['end_date', 'adults', 'children', 'sale_line_supplement_ids', 'supplier_id', 'product_id',
                       'api_model_id', 'destination_id']
        parent_node = doc.xpath("//group[@name='dynamic_fields']")
        if parent_node:
            parent_node = parent_node[0]
            sd = doc.xpath("//field[@name='start_date']")[0]
            ap = doc.xpath("//field[@name='api_model_id']")[0]
            ocg = sd.get('on_change', False)
            ctx = sd.get('context', False)
            ap = ap.get('context', False)
            ctx = self._update_ctx(ctx, ap)
            if flag:
                new_fields['api_model_id'] = res['fields']['api_model_id']
                new_fields['destination_id'] = res['fields']['destination_id']
                ctx = self._build_ctx(ctx, new_fields)
                del new_fields['api_model_id']
                del new_fields['destination_id']
            sd.set('context', ctx)
            for field in field_names:
                if field == 'sale_line_supplement_ids':
                    try:
                        ed = doc.xpath("//field[@name='" + field + "']")[0]
                        ed.set('context', ctx)
                    except IndexError:
                        field = 'product_package_supplement_ids'
                ed = doc.xpath("//field[@name='" + field + "']")[0]
                ed.set('context', ctx)
                if field == 'api_model_id' or field == 'destination_id':
                    ed.set('on_change', ocg)
                    trigger = ", 'trigger': " + field + "}"
                    ctx_trigger = ctx[::-1].replace('}', trigger[::-1], 1)[::-1]
                    ed.set('context', ctx_trigger)
            keys = new_fields.keys()
            keys.sort()
            for f in keys:
                n = etree.Element("field")
                n.set('name', f)
                modifiers = self._build_attr(cr, uid, f)
                n.set('modifiers', simplejson.dumps(modifiers))
                trigger = ", 'trigger': " + f + "}"
                ctx_trigger = ctx[::-1].replace('}', trigger[::-1], 1)[::-1]
                n.set('context', ctx_trigger)
                n.set('on_change', ocg)
                parent_node.append(n)
            res['arch'] = etree.tostring(doc)
        return res


class sale_order_line(Model):
    _name = 'sale.order.line'
    _inherit = 'sale.order.line'

    api_model_id = fields.Many2one('api.model', _('API'))

    api_model_name = fields.Char(related='api_model_id.api', string=_('Name'))

    destination_id = fields.Many2one('destination', _('City'))

    singleton_partner_id = None

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
                          uom=False, qty_uos=0, uos=False, name='', partner_id=False,
                          lang=False, update_tax=True, date_order=False, packaging=False,
                          fiscal_position=False, flag=False, context=None):
        if partner_id:
            self.singleton_partner_id = partner_id
        api_model = self.pool.get('api.model')
        dest_table = self.pool.get('destination')
        params = context.get('params', False)
        api_model_id = None
        destination_id = None
        if params:
            api_model_id = params.get('api_model_id', False)
            destination_id = params.get('destination_id', False)
            categ = params.get('category', '').lower()
            country = params.get('country', False)
            if country:
                country = dest_table.browse(cr, uid, country)
            else:
                try:
                    action = params['action']
                    if action == 308:
                        return super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty,
                                                                              uom, qty_uos,
                                                                              uos, name, partner_id, lang, update_tax,
                                                                              date_order,
                                                                              packaging, fiscal_position, flag, context)
                except KeyError:
                    pass
                raise except_orm(_('Error'), _('You must select a country'))
            api_model_id = api_model.search(cr, uid, [('id', '=', api_model_id)])
            api_model_id = api_model.browse(cr, uid, api_model_id)
        if api_model_id and api_model_id.api == 'local':
            return super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty, uom, qty_uos,
                                                                  uos, name, partner_id, lang, update_tax, date_order,
                                                                  packaging, fiscal_position, flag, context)
        else:
            dests = False
            domain = {}
            if api_model_id:
                obj_table = api_model.get_class_implementation(cr, uid, api_model_id.api)
                obj = obj_table.create({
                    'username': api_model_id.user,
                    'password': api_model_id.password,
                })
                dests = obj_table.get_destinations(country)
                if destination_id:
                    dest_ids = dest_table.search(cr, uid, [('id', '=', destination_id)])
                    dest = dest_table.browse(cr, uid, dest_ids)
                    method = 'get_all_' + categ + 's'
                    getattr(obj_table, method)(dest)
                    products = obj_table.get_products(categ, destination_id)
                    if products:
                        domain.update({'product_id': [('id', 'in', products)]})
            if dests:
                domain.update({'destination_id': [('id', 'in', [x.id for x in dests])]})
            res = {'domain': {}, 'value': {}}
            if partner_id:
                res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty, uom,
                                                                     qty_uos,
                                                                     uos, name, partner_id, lang, True, date_order,
                                                                     packaging, fiscal_position, True, context)
            res['domain'].update(domain)
            res['value']['product_id'] = product
            res['value']['product_uom_qty'] = qty
            res['value']['product_uos_qty'] = qty_uos
            res['value']['product_uom'] = uom
            res['value']['product_uos'] = uos
            res['value']['name'] = name
            # res['value']['customer_id'] = partner_id or self.singleton_partner_id
            res['value']['price_unit'] = 1.0
            res['value']['price_unit_cost'] = 1.0
            print 'Partner id: ' + str(partner_id)
            print 'Singleton Partner id: ' + str(self.singleton_partner_id)
            return res


class res_partner(Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    api_model = fields.Boolean(_('Is API?'), default=False)
