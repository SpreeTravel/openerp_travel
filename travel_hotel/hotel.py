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

import datetime as dt

from openerp.osv import fields
from openerp.osv.orm import Model
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF

ROOM = {1: 'simple', 2: 'price', 3: 'triple'}


class product_hotel(Model):
    _name = 'product.hotel'
    _inherits = {'product.product': 'product_id'}
    _inherit = ['mail.thread']

    _columns = {
        'product_id': fields.many2one('product.product', 'Product',
                                      required=True, ondelete="cascade"),
        'res_partner_id': fields.many2one('res.partner', 'Contact'),
        'chain_id': fields.many2one('res.partner', 'Chain'),
        'stars': fields.selection([('1', '1'), ('2', '2'), ('3', '3'),
                                   ('4', '4'), ('5', '5')], 'Stars'),
        'destination': fields.many2one('destination', 'Destination'),
        'hotel_name': fields.related('product_id', 'name', type='char',
                                     string='Name', size=128, select=True,
                                     store=True)
    }

    def price_get_partner(self, cr, uid, cls, to_search, params, context=None):
        sr = self.pool.get('sale.rooming')
        rooming = params.get('hotel_1_rooming_ids', [])

        price = 0.0
        model = self.pool.get(cls)
        to_search_sup = [x for x in to_search]

        if params['start_date'] and params['end_date']:
            occupation = sr.extract_values(cr, uid, rooming, context)
            for occ in occupation:
                if occ['room_type_id']:
                    to_search.append(('room_type_id', '=', occ['room_type_id']))
                pp_ids = model.search(cr, uid, to_search, context=context)
                if pp_ids:
                    pp = model.browse(cr, uid, pp_ids[0], context)
                    r_price = 0.0
                    if occ['adults'] <= 3:
                        room = occ['room'] == 'double' and 'price' or occ['room']
                        r_price += getattr(pp, room) * occ['adults']
                    else:
                        extra = self.get_percent_or_int(pp.price, pp.extra_adult)
                        r_price += (pp.price * 2 + (occ['adults'] - 2) * extra)
                    if occ['children'] == 1:
                        r_price += self.get_percent_or_int(pp.price, pp.child)
                    if occ['children'] == 2:
                        r_price += self.get_percent_or_int(pp.price, pp.child)
                        r_price += self.get_percent_or_int(pp.price, pp.second_child)
                    r_price *= occ['quantity']
                    price += r_price
            dsdate = dt.datetime.strptime(params['start_date'], DF)
            dedate = dt.datetime.strptime(params['end_date'], DF)
            price *= (dedate - dsdate).days
            price += self.price_get_partner_supp(cr, uid, pp, params,
                                                 to_search_sup, context)
        return price

    def price_get_partner_supp(self, cr, uid, pp, params, to_search_sup,
                               context=None):
        price = 0.0
        if params.get('supplement_ids', False):
            supp_ids = params['supplement_ids'][0][2]
            if supp_ids:
                prs = self.pool.get('product.rate.supplement')
                to_search_sup.append(('supplement_id', 'in', supp_ids))
                prs_ids = prs.search(cr, uid, to_search_sup, context=context)
                for supp in prs.browse(cr, uid, prs_ids, context):
                    rate_ids = [r.id for r in supp.rate_ids]
                    if not rate_ids or pp.product_rate_id.id in rate_ids:
                        price += supp.price
        return price

    def get_percent_or_int(self, adult_price, val):
        if val == 1:
            return 0.0
        elif val > 1:
            return val
        else:
            return adult_price * val

    _order = 'hotel_name asc'


class product_rate(Model):
    _name = 'product.rate'
    _inherit = 'product.rate'

    def _get_occupation(self, cr, uid, ids, fields, args, context=None):
        res = {}
        product = self.pool.get('product.product')
        order_line = self.pool.get('sale.order.line')
        pricelist = self.pool.get('pricelist.partnerinfo')
        for obj in self.browse(cr, uid, ids, context):
            res[obj.id] = 0
            pp_id = pricelist.search(cr, uid, [('product_rate_id', '=', obj.id)], context=context)
            pp = pricelist.browse(cr, uid, pp_id[0], context)
            tmpl_id = pp.suppinfo_id.product_id.id
            product_id = product.search(cr, uid, [('product_tmpl_id', '=', tmpl_id)], context=context)[0]
            to_search = [
                ('product_id', '=', product_id),
                ('start_date', '>=', obj.start_date),
                ('end_date', '<=', obj.end_date),
                ('state', 'not in', ['draft', 'cancel'])
            ]
            ol_ids = order_line.search(cr, uid, to_search, context=context)
            for ol in order_line.browse(cr, uid, ol_ids, context=context):
                for rooming in ol.hotel_1_rooming_ids:
                    if rooming.room_type_id.id == obj.room_type_id.id:
                        res[obj.id] += obj.quantity
        return res

    _columns = {
        'room_type_id': fields.many2one('option.value', 'Room',
                            domain="[('option_type_id.code', '=', 'rt')]"),
        'meal_plan_id': fields.many2one('option.value', 'Plan',
                            domain="[('option_type_id.code', '=', 'mp')]"),
        'simple': fields.float('Simple'),
        'triple': fields.float('Triple'),
        'extra_adult': fields.float('Extra Adult'),
        'second_child': fields.float('Second Child'),
        'allotment': fields.integer('Allotment'),
        'occupation': fields.function(_get_occupation, method=True,
                                      type='integer', string='Occupation')
    }
