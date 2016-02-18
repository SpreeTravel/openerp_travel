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
from openerp import fields, api
from openerp.models import Model
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.translate import _

ROOM = {1: 'simple', 2: 'price', 3: 'triple'}


class product_hotel(Model):
    _name = 'product.hotel'
    _inherits = {'product.product': 'product_id'}
    _inherit = ['mail.thread']

    product_id = fields.Many2one('product.product', _('Product'), required=True, ondelete="cascade")
    res_partner_id = fields.Many2one('res.partner', _('Contact'))
    chain_id = fields.Many2one('res.partner', _('Chain'))
    stars = fields.Selection([('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')], _('Stars'))
    destination = fields.Many2one('destination', _('Destination'))
    hotel_name = fields.Char(related='product_id.name', string=_('Name'), size=128, select=True, store=True)

    @api.multi
    def unlink(self):
        for x in self:
            product_product = self.env['product.product']
            pp = product_product.search([('id', '=', x.product_id.id)])
            pp.unlink()
        return super(product_hotel, self).unlink()

    def price_get_partner(self, cr, uid, cls, to_search, params, context=None):
        sr = self.pool.get('sale.rooming')
        rooming = params.get('hotel_1_rooming_ids', [])

        price = 0.0
        model = self.pool.get(cls)
        to_search_sup = [x for x in to_search if x[0].lower() != 'meal_plan_id']

        if params.get('start_date', False) and params.get('end_date', False):
            occupation = sr.extract_values(cr, uid, rooming, context)
            pp = False
            for occ in occupation:
                if occ['room_type_id']:
                    pp_ids = model.search(cr, uid, to_search + [('room_type_id', '=', occ['room_type_id'])],
                                          context=context)
                    for pp_id in pp_ids:
                        pp = model.browse(cr, uid, pp_id, context)
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
                        dsdate = dt.datetime.strptime(params['start_date'], DF)
                        dedate = dt.datetime.strptime(params['end_date'], DF)
                        isdate = dt.datetime.strptime(pp.start_date, DF)
                        iedate = dt.datetime.strptime(pp.end_date, DF)
                        ini = max(isdate, dsdate)
                        end = min(iedate, dedate)
                        if end != dedate:
                            r_price *= (end - ini).days + 1
                        else:
                            r_price *= (end - ini).days
                        price += r_price
            if pp:
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

    def get_option_type_fields(self, cr, uid, product_id, context):
        '''
        Dict of the model option_type values to load on sale_order view
        '''
        return [{'meal_plan_id': 'hotel_2_meal_plan_id'}, []]

    _order = 'hotel_name asc'


class product_rate(Model):
    _name = 'product.rate'
    _inherit = 'product.rate'

    room_type_id = fields.Many2one('option.value', _('Room'), domain="[('option_type_id.code', '=', 'rt')]")
    meal_plan_id = fields.Many2one('option.value', _('Plan'), domain="[('option_type_id.code', '=', 'mp')]")
    simple = fields.Float(_('Simple'))
    triple = fields.Float(_('Triple'))
    extra_adult = fields.Float(_('Extra Adult'))
    second_child = fields.Float(_('Second Child'))
