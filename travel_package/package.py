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

class product_package_line(Model):
    _name = 'product.package.line'
    _columns = {
        'product_id': fields.many2one('product.product', 'Product',
                                      required=True, ondelete="cascade"),
        'package_id': fields.many2one('product.package', 'Package', 
                                      required=True, ondelete="cascade"),
        'start_day': fields.integer('Start day'),
        'end_day': fields.integer('End day')
                }
    

class product_package(Model):
    _name = 'product.package'
    _inherits = {'product.product': 'product_id'}
    _inherit = ['mail.thread']

    _columns = {
        'product_id': fields.many2one('product.product', 'Product',
                                      required=True, ondelete="cascade"),
        'package_name': fields.related('product_id', 'name', type='char',
                                     string='Name', size=128, select=True,
                                     store=True),
        'product_line_ids': fields.one2many('product.package.line', 'package_id', 'Package')
    }

    def price_get_partner(self, cr, uid, cls, to_search, params, context=None):

        price = 0.0
        model = self.pool.get(cls)
        to_search_sup = [x for x in to_search]

        adults = params.get('adults', 0)
        children = params.get('children', 0)
        single = params.get('package_1_single', 0)
        double = params.get('package_2_double', 0)
        paxs = adults + children
        pp = False
        to_search += [('min_paxs', '<=', paxs), ('max_paxs', '>=', paxs)]
        for room in [('single', 1, single), ('double', 2, double)]:
            pp_ids = model.search(cr, uid, to_search+[('room', '=', room[0])], context=context)
            if len(pp_ids) == 1:
                pp = model.browse(cr, uid, pp_ids[0], context)
                price += pp.price * room[1] * room[2]
        
        if pp:
            price += self.price_get_partner_supp(cr, uid, pp, params, to_search_sup, context)

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
        
    def get_option_type_fields(self, cr, uid, product_id, context):
        '''
        Dict of the model option_type values to load on sale_order view
        '''
        return [{}, []]
        
    _order = 'package_name asc'


class product_rate(Model):
    _name = 'product.rate'
    _inherit = 'product.rate'
    _columns = {
        'min_paxs': fields.integer('Min Paxs'),
        'max_paxs': fields.integer('Max Paxs'),
        'room': fields.selection([('single', 'Single'),
                                  ('double', 'Double'),
                                  ('triple', 'Triple')], 'Room')
    }


class sale_context(Model):
    _name = 'sale.context'
    _inherit = 'sale.context'
    _columns = {
        'package_1_single': fields.integer('Single'),
        'package_2_double': fields.integer('Double'),
        'package_3_triple': fields.integer('Triple'),
    }
