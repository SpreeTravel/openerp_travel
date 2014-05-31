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


class product_car(Model):
    _name = 'product.car'
    _inherits = {'product.product': 'product_id'}
    _inherit = ['mail.thread']
    _columns = {
        'product_id': fields.many2one('product.product', 'Product',
                                      required=True, ondelete="cascade"),
        'car_name': fields.related('product_id', 'name', type='char',
                                   string='Name', size=128, select=True,
                                   store=True),
    }

    def price_get_partner(self, cr, uid, cls, to_search, params, context=None):
        price = 0.0
        model = self.pool.get(cls)
        to_search_sup = [x for x in to_search]

        if params['start_date'] and params['end_date']:
            dsdate = dt.datetime.strptime(params['start_date'], DF)
            dedate = dt.datetime.strptime(params['end_date'], DF)
            days = (dedate - dsdate).days
            to_search += [('min_days', '<=', days), ('max_days', '>=', days)]
            pp_ids = model.search(cr, uid, to_search, context=context)
            if pp_ids:
                pp = model.browse(cr, uid, pp_ids[0], context)
                price = pp.price * days
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

    _order = 'car_name asc'


class product_rate(Model):
    _name = 'product.rate'
    _inherit = 'product.rate'
    _columns = {
        'min_days': fields.integer('Min Days'),
        'max_days': fields.integer('Max Days'),
        'model_id': fields.many2one('option.value', 'Model',
                               domain="[('option_type_id.code', '=', 'md')]"),
        'transmission_id': fields.many2one('option.value', 'Transmission',
                               domain="[('option_type_id.code', '=', 'tm')]")
    }


class sale_context(Model):
    _name = 'sale.context'
    _inherit = 'sale.context'
    _columns = {
        'car_1_model_id': fields.many2one('option.value', 'Model',
                               domain="[('option_type_id.code', '=', 'md')]"),
        'car_2_transmission_id': fields.many2one('option.value',
                                                 'Transmission',
                               domain="[('option_type_id.code', '=', 'tm')]")
    }
