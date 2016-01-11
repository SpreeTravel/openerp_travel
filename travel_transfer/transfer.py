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

from openerp.osv import fields
from openerp.osv.orm import Model


class product_transfer(Model):
    _name = 'product.transfer'
    _inherits = {'product.product': 'product_id'}
    _inherit = ['mail.thread']
    _columns = {
        'product_id': fields.many2one('product.product', 'Product',
                                      required=True, ondelete="cascade"),
        'transfer_name': fields.related('product_id', 'name', type='char',
                                        string='Name', size=128, select=True,
                                        store=True),
        'origin': fields.many2one('destination', 'Origin'),
        'to': fields.many2one('destination', 'To')
    }

    def price_get_partner(self, cr, uid, cls, to_search, params, context=None):
        price = 0.0
        model = self.pool.get(cls)
        to_search_sup = [x for x in to_search]
        
        ov = self.pool.get('option.value')
        taxi = False
        if params.get('transfer_1_vehicle_type_id', False):
            vehicle_type = ov.browse(cr, uid, params['transfer_1_vehicle_type_id'], context=context)
            if vehicle_type.code == 'taxi':
                taxi = True

            adults = params.get('adults', 0)
            children = params.get('children', 0)
            paxs = adults + children
            to_search += [('min_paxs', '<=', paxs), ('max_paxs', '>=', paxs)]
            pp_ids = model.search(cr, uid, to_search, context=context)
            if len(pp_ids) == 1:
                pp = model.browse(cr, uid, pp_ids[0], context)
                if taxi:
                    price = pp.price
                else:
                    price = pp.price * adults + pp.price * children
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
          
    def get_option_type_fields(self, cr, uid, product_id, context):
        '''
        Dict of the model option_type values to load on sale_order view
        '''
        params  = context['params']
        fields = {'vehicle_type_id': 'transfer_1_vehicle_type_id', 
                  'guide_id': 'transfer_2_guide_id', 
                  'confort_id': 'transfer_3_confort_id'}
        adults = params.get('adults', 0)
        children = params.get('children', 0)
        paxs = adults + children
        filter = [('min_paxs', '<=', paxs), ('max_paxs', '>=', paxs)]
                
        return [fields, filter]

    _order = 'transfer_name asc'

    def unlink(self, cr, uid, ids, context=None):
        context = dict(context or {})
        product = self.browse(cr, uid, ids, context).product_id.id
        self.pool.get('product.product').unlink(cr, uid, product, context)
        return super(product_transfer,self).unlink(cr, uid, ids, context)

class product_rate(Model):
    _name = 'product.rate'
    _inherit = 'product.rate'
    _columns = {
        'min_paxs': fields.integer('Min Paxs'),
        'max_paxs': fields.integer('Max Paxs'),
        'vehicle_type_id': fields.many2one('option.value', 'Type',
                            domain="[('option_type_id.code', '=', 'vt')]"),
        'guide_id': fields.many2one('option.value', 'Guide',
                            domain="[('option_type_id.code', '=', 'guide')]"),
        'confort_id': fields.many2one('option.value', 'Confort',
                            domain="[('option_type_id.code', '=', 'vc')]")
    }


class sale_context(Model):
    _name = 'sale.context'
    _inherit = 'sale.context'
    _columns = {
        'transfer_1_vehicle_type_id': fields.many2one('option.value', 'Type',
                            domain="[('option_type_id.code', '=', 'vt')]"),
        'transfer_2_guide_id': fields.many2one('option.value', 'Guide',
                            domain="[('option_type_id.code', '=', 'guide')]"),
        'transfer_3_confort_id': fields.many2one('option.value', 'Confort',
                            domain="[('option_type_id.code', '=', 'vc')]")
    }
