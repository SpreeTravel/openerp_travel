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

import datetime
from openerp.osv import fields
from openerp.osv.orm import Model


class product_category(Model):
    _name = 'product.category'
    _inherit = 'product.category'

    def name_get(self, cr, uid, ids, context=None):
        if isinstance(ids, (list, tuple)) and not len(ids):
            return []
        if isinstance(ids, (long, int)):
            ids = [ids]
        reads = self.read(cr, uid, ids, ['name'], context=context)
        return [(r['id'], r['name']) for r in reads]

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)

    _columns = {
        'complete_name': fields.function(_name_get_fnc, type="char",
                                         string='Name'),
        'voucher_name': fields.char('Voucher name', size=64),
        'model_name': fields.char('Model name', size=64)
    }    
    
    _defaults = {
        'voucher_name': 'default_travel_voucher_report'
    }


class product_product(Model):
    _name = 'product.product'
    _inherit = 'product.product'

    def _get_reservations(self, cr, uid, ids, fields, args, context=None):
        result = {}
        order_line = self.pool.get('sale.order.line')
        for obj in self.browse(cr, uid, ids, context):
            to_search = [
                ('product_id', '=', obj.id),
                ('start_date', '>=', datetime.datetime.today())
            ]
            l_ids = order_line.search(cr, uid, to_search, context=context)
            result[obj.id] = l_ids
        return result

    _columns = {
        'reservation_ids':
            fields.function(_get_reservations, method=True, type='many2many',
                            relation='sale.order.line', string='Reservations')
    }

    def _get_category(self, cr, uid, context=None):
        context = context or {}
        name = context.get('category', False)
        imd = self.pool.get('ir.model.data')
        imd_ids = imd.search(cr, uid, [('name', '=', name)], context=context)
        res = False
        if imd_ids:
            res = imd.read(cr, uid, imd_ids[0], ['res_id'], context)['res_id']
        return res

    _defaults = {
        'type': 'service',
        'categ_id': _get_category
    }

    def price_get_partner(self, cr, uid, pid, suppinfo, params, context=None):
        context = context or {}
        cls = 'pricelist.partnerinfo'
        to_srch = [('suppinfo_id', '=', suppinfo)]
        if params.get('start_date', False) and params.get('end_date', False):
            sdate = params['start_date']
            edate = params['end_date']
            to_srch += ['|', '|', '&', ('start_date', '>=', sdate), ('start_date', '<=', edate),
                                  '&', ('end_date', '>=', sdate), ('end_date', '<=', edate),
                             '|', '&', ('start_date', '<=', sdate), ('end_date', '>=', sdate),
                                  '&',  ('start_date', '<=', edate), ('end_date', '>=', edate),]
        categ = self.browse(cr, uid, pid, context).categ_id.name.lower()
        for k, v in params.items():
            if k.startswith(categ) and k.endswith('_id') and params[k]:
                to_srch.append((k[len(categ) + 3:], '=', v))
        klas = self.pool.get('product.' + categ)
        args = [cr, uid, cls, to_srch, params, context]
        return getattr(klas, 'price_get_partner')(*args)


class product_supplierinfo(Model):
    _name = 'product.supplierinfo'
    _inherit = 'product.supplierinfo'
    _columns = {
        'supplement_ids': fields.one2many('product.rate.supplement',
                                          'suppinfo_id',
                                          'Supplements'),
                  'info': fields.text('Additional Information'),
        'currency_cost_id': fields.many2one('res.currency', 'Currency Cost')
    }
    _defaults = {
        'min_qty': 0.0
    }


class product_rate(Model):
    _name = 'product.rate'

    def _get_ref(self, cr, uid, ids, fields, args, context=None):
        result = {}
        for obj in self.browse(cr, uid, ids, context):
            result[obj.id] = 'PR-' + str(obj.id)
        return result

    _columns = {
        'reference': fields.function(_get_ref, method=True, type='char',
                                     size=256, string='Ref'),
        'start_date': fields.date('Start'),
        'end_date': fields.date('End'),
        'child': fields.float('Child'),
        'per_pax': fields.boolean('Per Pax')
    }

    _defaults = {
        'per_pax': 1
    }


class product_rate_supplement(Model):
    _name = 'product.rate.supplement'
    _columns = {
        'supplement_id': fields.many2one('option.value', 'Supplement',
                            domain="[('option_type_id.code', '=', 'sup')]"),
        'start_date': fields.date('Start date'),
        'end_date': fields.date('End date'),
        'price': fields.float('Price'),
        'suppinfo_id': fields.many2one('product.supplierinfo',
                                           'Supplier'),
        'rate_ids': fields.many2many('product.rate', 'supplements_rates_rel',
                                     'supplement_id', 'rate_id', 'Rates')
    }


class pricelist_partnerinfo(Model):
    _name = 'pricelist.partnerinfo'
    _rec_name = 'reference'
    _inherit = 'pricelist.partnerinfo'
    _inherits = {'product.rate': 'product_rate_id'}
    _columns = {
        'product_rate_id': fields.many2one('product.rate', 'Product Rate',
                                           ondelete="cascade", select=True),
        'rate_start_date': fields.related('product_rate_id', 'start_date',
                                          string='Start Date', type='date',
                                          store=True),
        'product_id': fields.related('suppinfo_id', 'product_id',
                                     string='Product', type='many2one',
                                     relation='product.template'),
        'sequence': fields.integer('Sequence')
    }
    _defaults = {
        'min_quantity': 0.0,
        'sequence': 0
    }
    _order = 'rate_start_date'
