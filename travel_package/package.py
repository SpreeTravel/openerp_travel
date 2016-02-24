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
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF

ROOM = {1: 'simple', 2: 'price', 3: 'triple'}


class product_package_line(Model):
    _name = 'product.package.line'

    _order = 'order'

    @api.model
    def get_default(self):
        package_lines = self.env['product.package.line']
        try:
            tmp_lines = self.env.context['lines']
            tmp_lines = [x for x in tmp_lines if not x[0]]
        except KeyError:
            tmp_lines = False
        try:
            _id = self.env.context['package_id']
        except KeyError:
            _id = False
        lines = package_lines.search([('package_id', '=', _id)])
        _max = max(lines, key=lambda y: y.order).order if len(lines) else 0
        if tmp_lines:
            return _max + len(tmp_lines) + 1
        else:
            return _max + 1

    @api.multi
    def compute_function(self):
        package_lines = self.env['product.package.line']
        try:
            _id = self[0].package_id.id
        except KeyError:
            _id = False
        lines = package_lines.search([('package_id', '=', _id)])
        _max = max(lines, key=lambda y: y.order).order if len(lines) else 0
        _max += 1
        for x in self:
            if not x.order:
                x.order = _max
                _max += 1

    product_id = fields.Many2one('product.product', _('Product'), required=True, ondelete="cascade")
    category_id = fields.Many2one('product.category', _('Category'), required=True, ondelete='cascade')
    supplier_id = fields.Many2one('res.partner', _('Supplier'), ondelete='cascade')
    package_id = fields.Many2one('product.package', _('Package'), required=True, ondelete="cascade")
    num_day = fields.Integer(_('Number of Days'), default=1)
    order = fields.Integer(string=_('Order'), default=get_default)

    product_package_line_conf_id = fields.Many2one('product.package.line.conf', _('Configuration'))

    @api.onchange('category_id')
    def set_supplier_product(self):
        category_table = self.env['product.template']
        products = category_table.search([('categ_id', '=', self.category_id.id)])
        res = {
            'product_id': [('id', 'in', [x.id for x in products])]
        }
        supplier_info_table = self.env['product.supplierinfo']
        supplier = supplier_info_table.search([('product_tmpl_id', 'in', [x.id for x in products])])
        res.update({
            'supplier_id': [('id', 'in', [x.name.id for x in supplier])]
        })
        self.supplier_id = False
        self.product_id = False
        return {
            'domain': res
        }

    @api.onchange('product_id')
    def set_supplier(self):
        if self.product_id.id and self.category_id.id:
            supplier_info_table = self.env['product.supplierinfo']
            supplier = supplier_info_table.search([('product_tmpl_id', '=', self.product_id.id)])
            self.supplier_id = False
            return {
                'domain': {
                    'supplier_id': [('id', 'in', [x.name.id for x in supplier])]
                }

            }
        elif self.category_id.id and not self.product_id.id:
            return self.set_supplier_product()
        elif not self.category_id.id and self.product_id.id:
            supplier_info_table = self.env['product.supplierinfo']
            supplier = supplier_info_table.search([('product_tmpl_id', '=', self.product_id.id)])
            self.supplier_id = False
            return {
                'domain': {
                    'supplier_id': [('id', 'in', [x.name.id for x in supplier])]
                }
            }
        return {}

    @api.onchange('order')
    def verify_order(self):
        package_lines = self.env['product.package.line']
        try:
            _id = self.env.context['package_id']
        except KeyError:
            _id = False
        lines = package_lines.search([('package_id', '=', _id)])
        warn_msg = None
        line_id = self.env.context.get('id', False)
        repeated = []
        for x in lines:
            if x.id != line_id:
                if x.order in repeated:
                    warn_msg = _('Order field can not be repeated, must be unique!!!!')
                    break
                else:
                    repeated.append(x.order)
        if self.order in repeated:
            warn_msg = _('Order field can not be repeated, must be unique!!!!')
        if self.order < 1:
            warn_msg = _('Order field must be greater than 0!!!!')
        if warn_msg:
            warning = {
                'title': _('Configuration Error!'),
                'message': warn_msg
            }
            return {'warning': warning}

    @api.onchange('num_day')
    def fix_num_day(self):
        if self.num_day < 1:
            self.num_day = 1
            return {
                'warning': {
                    'title': _('Configuration Error!'),
                    'message': _('The number of day must be greater than 0')
                }
            }

    def _get_max_min(self):
        lines_table = self.env['product.package.line']
        lines = lines_table.search([('package_id', '=', self.package_id.id)])
        return max(lines, key=lambda x: x.order).order, min(lines, key=lambda x: x.order).order

    @api.multi
    def up(self):
        obj = self[0]
        _max, _min = self._get_max_min()
        if self.order == _min:
            return
        else:
            lines_table = self.env['product.package.line']
            line = lines_table.search([('order', '=', obj.order - 1), ('package_id', '=', obj.package_id.id)])
            line.write({'order': line.order + 1})
            self.write({'order': obj.order - 1})
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'product.package',
                'res_id': obj.package_id.id
            }

    @api.multi
    def down(self):
        obj = self[0]
        _max, _min = self._get_max_min()
        if self.order == _max:
            return
        else:
            lines_table = self.env['product.package.line']
            line = lines_table.search([('order', '=', obj.order + 1), ('package_id', '=', obj.package_id.id)])
            line.write({'order': line.order - 1})
            self.write({'order': obj.order + 1})
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'product.package',
                'res_id': obj.package_id.id
            }

    @api.multi
    def edit(self):
        obj = self[0]
        res_id = None
        if obj.product_package_line_conf_id.id:
            res_id = obj.product_package_line_conf_id
        else:
            element = obj.product_package_line_conf_id.create({
                'product_package_line_id': obj.id,
                'product_id': obj.product_id.id,
                'category_id': obj.category_id.id,
                'supplier_id': obj.supplier_id.id
            })
            res_id = obj.product_package_line_conf_id = element
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'flags': {'form': {'action_buttons': True}},
            'res_model': 'product.package.line.conf',
            'res_id': res_id.id
        }

        # _defaults = {
        #     'order': get_default
        # }

    @api.model
    def create(self, vals):
        print 'Pass here'
        return super(product_package_line, self).create(vals)


class product_package(Model):
    _name = 'product.package'
    _inherits = {'product.product': 'product_id'}
    _inherit = ['mail.thread']

    product_id = fields.Many2one('product.product', _('Product'),
                                 required=True, ondelete="cascade")
    package_name = fields.Char(related='product_id.name', string=_('Name'), size=128, select=True,
                               store=True)
    product_line_ids = fields.One2many('product.package.line', 'package_id', _('Package'))

    def price_get_partner(self, cr, uid, cls, to_search, params, context=None):

        price = 0.0
        model = self.pool.get(cls)
        to_search_sup = [x for x in to_search]

        adults = params.get('adults', 0)
        children = params.get('children', 0)
        paxs = adults + children
        pp = False
        to_search += [('min_paxs', '<=', paxs), ('max_paxs', '>=', paxs)]
        pp_ids = model.search(cr, uid, to_search, context=context)
        if len(pp_ids) == 1:
            pp = model.browse(cr, uid, pp_ids[0], context)
            price += pp.price
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

    min_paxs = fields.Integer(_('Min Paxs'))
    max_paxs = fields.Integer(_('Max Paxs'))


class sale_context(Model):
    _name = 'sale.context'
    _inherit = 'sale.context'


class product_package_line_conf(Model):
    _name = 'product.package.line.conf'
    _inherits = {'sale.context': 'sale_context_id'}

    product_package_line_id = fields.Many2one('product.package.line', _('Line'))

    product_id = fields.Many2one(related='product_package_line_id.product_id', string=_('Product'), store=True)

    category_id = fields.Many2one(related='product_package_line_id.category_id', string=_('Category'), store=True)

    category = fields.Char(related='category_id.name', string=_('Category'), store=True)

    supplier_id = fields.Many2one(related='product_package_line_id.supplier_id', string=_('Supplier'), store=True)

    name = fields.Text(_('Description'))

    adults = fields.Integer(_('Adults'))

    product_package_supplement_ids = fields.Many2many('option.value', 'product_package_supplement_rel',
                                                      'product_package_id', 'option_value_id',
                                                      _('Supplements'),
                                                      domain="[('option_type_id.code', '=', 'sup')]")

    children = fields.Integer(_('Children'))

    # sale_context_id = fields.Many2one('sale.context', _('Sale Context'), ondelete="cascade", select=True)#
    start_date = fields.Date(_('In'), store=True)

    end_date = fields.Date(_('Out'), store=True)

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        context = context or {}
        res = super(product_package_line_conf, self).fields_view_get(cr, uid, view_id,
                                                                     view_type, context=context, toolbar=toolbar,
                                                                     submenu=submenu)
        if view_type == 'form':
            sc = self.pool.get('sale.context')
            res = sc.update_view_with_context_fields(cr, uid, res, context, flag=False)
        return res
