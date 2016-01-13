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
import datetime as dt
from lxml import etree
from openerp import fields, api
from openerp.models import Model
from openerp.exceptions import except_orm
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp


class supplier_price(Model):
    _name = 'supplier.price'

    sale_order_line = fields.Many2one('sale.order.line')
    supplier = fields.Char(_('Supplier'))
    price = fields.Char(_('Price'))


class sale_order(Model):
    _name = 'sale.order'
    _inherit = 'sale.order'

    @api.one
    def _get_lead_name(self):
        self.lead_name = min(self.pax_ids).name if self.pax_ids else False

    # @api.model
    # def _get_lead_name(self, cr, uid, ids, fields, args, context=None):
    #     result = {}
    #     for obj in self.browse(cr, uid, ids, context):
    #         result[obj.id] = False
    #         if obj.pax_ids:
    #             min = obj.pax_ids[0]
    #             for pax in obj.pax_ids:
    #                 if pax.id < min.id:
    #                     min = pax
    #             result[obj.id] = min.name
    #
    #     return result

    def get_today(self):
        return dt.date.today()

    def _lead_name_search(self, cr, uid, obj, field_name, args, context=None):
        name = args[0][2]
        values = []
        ids = self.search(cr, uid, [])
        for obj in self.browse(cr, uid, ids, context):
            if obj.pax_ids and name.lower() in obj.pax_ids[0].name.lower():
                values.append(obj.id)
        result = [('id', 'in', values)]
        return result

    def _get_total_paxs(self, cr, uid, ids, fields, args, context=None):
        result = {}
        for obj in self.browse(cr, uid, ids, context):
            result[obj.id] = False
            result[obj.id] = len(obj.pax_ids)

        return result

    date_order = fields.Date('Start Date', required=True, readonly=True, default=get_today,
                             select=True, states={'draft': [('readonly', False)],
                                                  'sent': [('readonly', False)]})
    end_date = fields.Date('End Date', required=True, readonly=True, select=True,
                           states={'draft': [('readonly', False)],
                                   'sent': [('readonly', False)]})
    flight_in = fields.Char('Flight In', size=64)
    flight_out = fields.Char('Flight Out', size=64)
    order_line = fields.One2many('sale.order.line', 'order_id', 'Order Lines', readonly=True,
                                 states={'draft': [('readonly', False)],
                                         'sent': [('readonly', False)],
                                         'manual': [('readonly', False)]})
    pax_ids = fields.Many2many('res.partner', 'sale_order_res_partner_pax_rel', 'order_id', 'pax_id', 'Paxs',
                               domain="[('pax', '=', True)]")
    total_paxs = fields.Integer(compute=_get_total_paxs, string='Total paxs', store=True)
    lead_name = fields.Char(compute=_get_lead_name, string='Lead Name', size=128,
                            search=_lead_name_search)

    # _defaults = {
    #
    #     'date_order': dt.date.today()
    # }

    _order = 'create_date desc'

    @api.multi
    def write(self, vals):
        res = super(sale_order, self).write(vals)
        if vals.get('state', False) in ['confirmed', 'done', 'cancel']:
            sol = self.env['sale.order.line']
            sol_ids = []
            for s in self:
                sol_ids += [sl.id for sl in s.order_line]
            if sol_ids:
                sol.write({'state': vals['state']})
        return res

    @api.multi
    def to_confirm(self):
        return self.write({'state': 'manual'})

    def to_cancel(self):
        return self.write({'state': 'cancel'})

    @api.onchange('end_date', 'start_date')
    def check_dates(self):
        if self.date_order > self.end_date:
            self.end_date = self.date_order


class sale_context(Model):
    _name = 'sale.context'

    @api.multi
    def _get_paxs(self):
        result = {}
        for obj in self:
            result[obj.id] = obj.adults + obj.children
        return result

    @api.multi
    def _get_duration(self):
        result = {}
        for obj in self:
            result[obj.id] = 1
            if obj.end_date:
                dsdate = dt.datetime.strptime(obj.start_date, DF)
                dedate = dt.datetime.strptime(obj.end_date, DF)
                result[obj.id] = (dedate - dsdate).days
        return result

    category_id = fields.Many2one('product.category', 'Category')
    category = fields.Char('Category', size=64)
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    duration = fields.Float(compute=_get_duration, method=True, type='float', string='Duration')
    adults = fields.Integer('Adults')
    children = fields.Integer('Children')
    start_time = fields.Char('Start Time', size=64)
    start_place = fields.Char('Start Place', size=255)
    end_time = fields.Char('End Time', size=64)
    end_place = fields.Char('End Place', size=255)
    supplier_id = fields.Many2one('res.partner', 'Supplier', domain="[('supplier', '=', True)]")
    reservation_number = fields.Char('Reservation', size=64)
    paxs = fields.Integer(compute=_get_paxs, method=True, string='Paxs', store=True)

    def get_supplier(self, obj):
        if obj.supplier_id:
            return obj.supplier_id
        elif obj.product_id.seller_id:
            return obj.product_id.seller_id
        else:
            raise except_orm(_('Error!'),
                             _("There is at least one sale order line without supplier"))

    def get_supplier_info_id(self, cr, uid, obj, context=None):
        supplierinfo_obj = self.pool.get('product.supplierinfo')
        supplier = self.get_supplier(obj)
        to_search = [
            ('name', '=', supplier.id),
            ('product_id', '=', obj.product_id.product_tmpl_id.id)
        ]
        sinfo = supplierinfo_obj.search(cr, uid, to_search, context=context)
        return sinfo and sinfo[0] or False

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

    def get_context_params(self, cr, uid, line, context=None):
        context_params = {}
        fields = self.get_context_fields(cr, uid, context)
        for f in fields:
            if hasattr(line, f):
                value = getattr(line, f)
                if value:
                    if fields[f]['type'] == 'many2one':
                        context_params.update({f: value.id})
                    else:
                        context_params.update({f: value})
        return context_params

    def update_view_with_context_fields(self, cr, uid, res, context=None):
        new_fields = self.get_context_fields(cr, uid, context)
        res['fields'].update(new_fields)
        doc = etree.XML(res['arch'])
        field_names = ['end_date', 'adults', 'children', 'sale_line_supplement_ids', 'supplier_id', 'product_id']
        parent_node = doc.xpath("//group[@name='dynamic_fields']")
        if parent_node:
            parent_node = parent_node[0]
            sd = doc.xpath("//field[@name='start_date']")[0]
            ocg = sd.get('on_change', False)
            ctx = sd.get('context', False)
            ctx = self._build_ctx(ctx, new_fields)
            sd.set('context', ctx)
            for field in field_names:
                ed = doc.xpath("//field[@name='" + field + "']")[0]
                ed.set('context', ctx)
            # ad = doc.xpath("//field[@name='adults']")[0]
            # ad.set('context', ctx)
            # ch = doc.xpath("//field[@name='children']")[0]
            # ch.set('context', ctx)
            # sp = doc.xpath("//field[@name='sale_line_supplement_ids']")[0]
            # sp.set('context', ctx)
            # sp = doc.xpath("//field[@name='supplier_id']")[0]
            # sp.set('context', ctx)
            # # sp = doc.xpath("//field[@name='product_uom_qty']")[0]
            # sp.set('context', ctx)
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


class sale_order_line(Model):
    _name = 'sale.order.line'
    _inherit = 'sale.order.line'
    _inherits = {'sale.context': 'sale_context_id'}

    resume_table_price = fields.One2many('supplier.price', 'sale_order_line', string='Prices')

    description = fields.Text('Description')

    sale_context_id = fields.Many2one('sale.context', 'Sale Context', ondelete="cascade", select=True)

    sale_line_supplement_ids = fields.Many2many('option.value', 'sale_line_option_value_rel', 'sale_line_id',
                                                'option_value_id', 'Supplements',
                                                domain="[('option_type_id.code', '=', 'sup')]")

    price_unit_cost = fields.Float('Cost Price', digits_compute=dp.get_precision('Product Price'))
    currency_cost_id = fields.Many2one('res.currency', 'Currency Cost')
    customer_id = fields.Many2one(related='order_id.partner_id', readonly=True,
                                  string='Customer', store=True)
    # TODO: Ver pq no se puede poner required
    order_start_date = fields.Date(related='order_id.date_order', string='In',
                                   store=True)
    # TODO: Ver pq no se puede poner required
    order_end_date = fields.Date(related='order_id.end_date', string='Out', store=True)

    # @api.model
    # def create(self, vals):
    #     return super(sale_order_line, self).create(vals)
    #
    # @api.multi
    # def write(self, vals):
    #     return super(sale_order_line, self).create(vals)

    def __init__(self, cr, uid):
        from openerp.addons.sale.sale import sale_order_line
        states = sale_order_line._columns['state'].selection
        try:
            states.remove(('request', 'Request!'))
            states.remove(('requested', 'Requested'))
        except:
            pass
        draft_idx = states.index(('draft', 'Draft'))
        states.insert(draft_idx + 1, ('request', 'Request!'))
        states.insert(draft_idx + 2, ('requested', 'Requested'))
        sale_order_line._columns['state'].selection = states
        return super(sale_order_line, self).__init__(cr, uid)

    def to_request(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'request'}, context)

    def to_requested(self):
        return self.write({'state': 'requested'})

    def to_confirm(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state': 'confirmed'}, context)

    def to_cancel(self):
        return self.write({'state': 'cancel'})

    @api.onchange('price_unit_cost', 'price_unit')
    def price_changes(self):
        warn_msg = None
        if self.price_unit_cost <= 0:
            warn_msg = _('Your cost price is lower or equal zero.')
        elif self.price_unit <= 0:
            warn_msg = _('Your sale price is lower or equal zero.')
        if self.price_unit_cost < self.price_unit:
            warn_msg = _('Your cost price is lower than your real price.')
        if warn_msg:
            warning = {
                'title': _('Configuration Error!'),
                'message': warn_msg
            }
            return {'warning': warning}

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
                          uom=False, qty_uos=0, uos=False, name='', partner_id=False,
                          lang=False, update_tax=True, date_order=False, packaging=False,
                          fiscal_position=False, flag=False, context=None):

        context = context or {}
        lang = lang or context.get('lang', False)
        if not partner_id:
            raise except_orm(_('No Customer Defined !'),
                             _('Before choosing a product,\n select a customer in the sales form.'))
        warning = {}
        product_uom_obj = self.pool.get('product.uom')
        partner_obj = self.pool.get('res.partner')
        product_obj = self.pool.get('product.product')
        supplier_id = context.get('supplier_id', False)
        params = context.get('params', {})
        context = {
            'lang': lang,
            'partner_id': partner_id,
            'supplier_id': supplier_id,
            'params': params
        }
        if partner_id:
            lang = partner_obj.browse(cr, uid, partner_id).lang
        context_partner = {'lang': lang, 'partner_id': partner_id}

        if not product:
            return {'value': {'th_weight': 0,
                              'product_uos_qty': qty}, 'domain': {'product_uom': [],
                                                                  'product_uos': []}}
        if not date_order:
            date_order = time.strftime(DF)

        result = {}
        warning_msgs = ''
        product_obj = product_obj.browse(cr, uid, product,
                                         context=context_partner)
        uom2 = False
        if uom:
            uom2 = product_uom_obj.browse(cr, uid, uom)
            if product_obj.uom_id.category_id.id != uom2.category_id.id:
                uom = False
        if uos:
            if product_obj.uos_id:
                uos2 = product_uom_obj.browse(cr, uid, uos)
                if product_obj.uos_id.category_id.id != uos2.category_id.id:
                    uos = False
            else:
                uos = False
        afp = self.pool.get('account.fiscal.position')
        fpos = fiscal_position and afp.browse(cr, uid, fiscal_position) or False
        if update_tax:
            result['tax_id'] = afp.map_tax(cr, uid, fpos, product_obj.taxes_id)
        if not flag:
            pp = self.pool.get('product.product')
            result['name'] = pp.name_get(cr, uid, [product_obj.id],
                                         context=context_partner)[0][1]
            if product_obj.description_sale:
                result['name'] += '\n' + product_obj.description_sale
        domain = {}
        if (not uom) and (not uos):
            result['product_uom'] = product_obj.uom_id.id
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
                uos_category_id = product_obj.uos_id.category_id.id
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
                uos_category_id = False
            result['th_weight'] = qty * product_obj.weight
            domain = {'product_uom':
                          [('category_id', '=', product_obj.uom_id.category_id.id)],
                      'product_uos':
                          [('category_id', '=', uos_category_id)]}
        elif uos and not uom:
            result['product_uom'] = product_obj.uom_id and product_obj.uom_id.id
            result['product_uom_qty'] = qty_uos / product_obj.uos_coeff
            result['th_weight'] = result['product_uom_qty'] * product_obj.weight
        elif uom:
            default_uom = product_obj.uom_id and product_obj.uom_id.id
            q = product_uom_obj._compute_qty(cr, uid, uom, qty, default_uom)
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
            result['th_weight'] = q * product_obj.weight

        if not uom2:
            uom2 = product_obj.uom_id

        if not pricelist:
            warn_msg = _('You have to select a pricelist or a customer in the sales form !\n'
                         'Please set one before choosing a product.')
            warning_msgs += _("No Pricelist ! : ") + warn_msg + "\n\n"
        else:
            price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist],
                                                                 product, qty or 1.0, partner_id, {
                                                                     'uom': uom or result.get('product_uom'),
                                                                     'date': date_order,
                                                                     'supplier_id': supplier_id,
                                                                     'params': params
                                                                 })[pricelist]
            if price is False:
                warn_msg = _("Cannot find a pricelist line matching this product and quantity.\n"
                             "You have to change either the product, the quantity or the pricelist.")

                # warning_msgs += _("No valid pricelist line found ! :") + warn_msg +"\n\n"
            else:
                result.update({'price_unit': price})

            cost_price = self.show_cost_price(cr, uid, result, product, qty, partner_id, uom, date_order,
                                              supplier_id, params, pricelist, context)
            result.update({'price_unit_cost': cost_price})

        if warning_msgs:
            warning = {
                'title': _('Configuration Error!'),
                'message': warning_msgs
            }
        _args = (pricelist, product, qty, partner_id, uom, date_order, params)
        # This is for loading only available option values
        if context.get('params', False) and context['params'].get('category', False):
            options = self.get_available_options(cr, uid, product_obj.id, context, *_args)
            domain.update(options.get('domain', {}))
            result.update(options.get('value', {}))

        return {'value': result, 'domain': domain, 'warning': warning}

    def get_room_type_id(self, cr, uid):
        option_value = self.pool.get('option.value')
        values = option_value.search(cr, uid, [('option_type_id.code', '=', 'rt')])
        return values[0] if len(values) else False

    def get_supplier_name(self, cr, uid, _id):
        _model = self.pool.get('res.partner')
        _model_ids = _model.search(cr, uid, [('id', '=', _id)])
        res_partner = _model.browse(cr, uid, _model_ids)
        return res_partner.display_name

    def get_available_options(self, cr, uid, product_id, context, *args, **kwargs):
        '''
        Load only available values for the sale order form
        '''

        result = {}
        domain = {}

        # Automatically load supplier field values
        product_model = self.pool.get('product.product')
        try:
            _category = context['params']['category']
            if product_id and _category:
                try:
                    elements = context['params']['hotel_1_rooming_ids']
                    if not len(elements):
                        result.update(
                            {'hotel_1_rooming_ids': [[0, False,
                                                      {u'room_type_id': self.get_room_type_id(cr, uid),
                                                       u'quantity': 1,
                                                       u'children': 0, u'room': u'double', u'adults': 2}]]})
                except KeyError:
                    pass
        except KeyError:
            pass
        product_obj = product_model.browse(cr, uid, product_id, context)
        product_tmpl_id = product_obj.product_tmpl_id.id
        suppinfo_model = self.pool.get('product.supplierinfo')
        supp_domain = [('product_tmpl_id', '=', product_tmpl_id)]
        # if context.get('supplier_id', False):
        #   supp_domain = [('name', '=', context['supplier_id'])]
        _supplier_id = context.get('supplier_id', False)
        suppinfo_ids = suppinfo_model.search(cr, uid, supp_domain, context=context)
        suppinfos = suppinfo_model.browse(cr, uid, suppinfo_ids)

        product_rate_suplement = self.pool.get('product.rate.supplement')
        availables_suplements = product_rate_suplement.search(cr, uid, [('suppinfo_id', '=', suppinfo_ids)],
                                                              context=context)
        availables_suplements = product_rate_suplement.browse(cr, uid, availables_suplements)
        availables_suplements = list(set([int(s.supplement_id) for s in availables_suplements]))

        domain.update({'sale_line_supplement_ids': [('id', 'in', availables_suplements)]})
        # Automatically upload option_type values
        params = context.get('params')

        category_model = self.pool.get('product.category')
        category_obj = category_model.browse(cr, uid, product_obj.categ_id.id)
        model_name = category_obj.model_name
        if not model_name or model_name == '':
            model_name = category_obj.name.lower()

        product_specific_model = self.pool.get('product.' + model_name)
        free_fields, filter = product_specific_model.get_option_type_fields(cr, uid, product_id, context)
        field_ids = []
        for field_name, form_name in free_fields.iteritems():
            for suppinfo_id in suppinfo_ids:
                pricelist_model = self.pool.get('pricelist.partnerinfo')
                pricelist_ids = pricelist_model.search(cr, uid, filter + [('suppinfo_id', '=', suppinfo_id)],
                                                       context=context)
                field_ids = list(set([getattr(p, field_name).id for p in
                                      pricelist_model.browse(cr, uid, pricelist_ids, context=context)]))

                if len(field_ids) > 0:
                    if params.get(form_name, False):
                        if params[form_name] not in field_ids:
                            result.update({form_name: ''})
                            # elif len(pricelist_ids) == 1:
                            #     result.update({form_name: field_ids[0]})
            if len(field_ids):
                domain.update({form_name: [('id', 'in', field_ids)]})
            else:
                domain.update({form_name: False})

        try:
            tmp = context['params']['hotel_2_meal_plan_id']
            if tmp:
                product_rate_suplement = self.pool.get('product.rate')
                availables_meal_plan_ids = product_rate_suplement.search(cr, uid, [('meal_plan_id', '=', tmp)])
                availables_pricelist = list(
                    set([x.id for x in product_rate_suplement.browse(cr, uid, availables_meal_plan_ids)]))
                product_rate_suplement = self.pool.get('pricelist.partnerinfo')
                availables_pricelist_partnerinfos_ids = product_rate_suplement.search(cr, uid, [
                    ('product_rate_id', '=', availables_pricelist)])
                meal_plan_suppinfos_ids = [int(x.suppinfo_id) for x in product_rate_suplement.browse(cr, uid,
                                                                                                     availables_pricelist_partnerinfos_ids)]
                suppinfo_ids = list(set(suppinfo_ids).intersection(set(meal_plan_suppinfos_ids)))
        except KeyError:
            pass
        try:
            tmp = context['params']['supplement_ids']
            if type(tmp) is list:
                tmp = tmp[0][2]
                if tmp:
                    product_rate_suplement = self.pool.get('product.rate.supplement')
                    availables_suplements_ids = product_rate_suplement.search(cr, uid, [('supplement_id', '=', tmp)])
                    availables_suplements = product_rate_suplement.browse(cr, uid, availables_suplements_ids)
                    suplements_suppinfo_ids = [int(p.suppinfo_id) for p in availables_suplements]
                    suppinfo_ids = list(set(suppinfo_ids).intersection(set(suplements_suppinfo_ids)))
        except KeyError:
            pass

        suppinfos = suppinfo_model.browse(cr, uid, suppinfo_ids)
        tmp_list = [s.name.id for s in suppinfos]
        try:
            _category = context['params']['category']
            if product_id and _category:
                if args[0]:
                    results = []
                    for tmp_supplier in tmp_list:
                        price = self.pool.get('product.pricelist').price_get(cr, uid, [args[0]],
                                                                             args[1], args[2] or 1.0, args[3], {
                                                                                 'uom': args[4] or result.get(
                                                                                     'product_uom'),
                                                                                 'date': args[5],
                                                                                 'supplier_id': tmp_supplier,
                                                                                 'params': params
                                                                             })[args[0]]
                        results.append([0, False, {
                            u'price': price,
                            u'supplier': self.get_supplier_name(cr, uid, tmp_supplier)
                        }])
                    result.update(
                        {'resume_table_price': results})
        except KeyError:
            pass

        if _supplier_id not in tmp_list:
            result.update({'supplier_id': False})
        # if len(tmp_list) == 1:
        #     result.update({'supplier_id': tmp_list[0]})
        domain.update({'supplier_id': [('id', 'in', tmp_list)]})
        return {'value': result, 'domain': domain}

    def show_cost_price(self, cr, uid, result, product, qty, partner_id, uom,
                        date_order, supplier_id, params, pricelist,
                        context=None):
        pl_obj = self.pool.get('product.pricelist')
        cp_ids = pl_obj.search(cr, uid, [('name', '=', 'Cost Pricelist')],
                               context=context)
        if cp_ids:
            cp_id = cp_ids[0]
            cost_price = pl_obj.price_get(cr, uid, [cp_id],
                                          product, qty or 1.0, partner_id, {
                                              'uom': uom or result.get('product_uom'),
                                              'date': date_order,
                                              'supplier_id': supplier_id,
                                              'params': params
                                          })[cp_id]
            sale_currency_id = pl_obj.browse(cr, uid, pricelist).currency_id.id
            cost_currency_id = pl_obj.browse(cr, uid, cp_id).currency_id.id
            if sale_currency_id != cost_currency_id:
                cr_obj = self.pool.get('res.currency')
                cost_price = cr_obj.compute(cr, uid, cost_currency_id,
                                            sale_currency_id, cost_price,
                                            round=False, context=context)
            return cost_price
        return 0.0

    def fields_view_get(self, cr, uid, view_id=None, view_type='form',
                        context=None, toolbar=False, submenu=False):
        context = context or {}
        res = super(sale_order_line, self).fields_view_get(cr, uid, view_id,
                                                           view_type, context=context, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            sc = self.pool.get('sale.context')
            res = sc.update_view_with_context_fields(cr, uid, res, context)
        return res

    def onchange_category(self, cr, uid, ids, category_id, context=None):
        res = {}
        if category_id:
            category = self.pool.get('product.category')
            category_obj = category.browse(cr, uid, category_id)
            name = category_obj.model_name
            if not name or name == '':
                name = category_obj.name.lower()
            res['value'] = {'category': name}
        return res

    def default_currency_cost(self, cr, uid, context=None):
        company = self.pool.get('res.company')
        company_id = company._company_default_get(cr, uid, 'sale.order.line',
                                                  context=context)
        return company.browse(cr, uid, company_id).currency_id.id

    def go_to_order(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context)
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.order',
            'res_id': obj.order_id.id,
        }

    def get_total_paxs(self, cr, uid, params, context=None):
        return params.get('adults', 0) + params.get('children', 0)

    def get_margin_days(self, cr, uid, params, context=None):
        '''
        The number of days of the service countable for apply a per day margin
        '''
        days = 0
        if params.get('supplement_ids', False):
            ini = dt.datetime.strptime(params['start_date'], DF)
            end = dt.datetime.strptime(params['end_date'], DF)
            days = (end - ini).days + 1
        return days

    def print_voucher(self, cr, uid, ids, context=None):

        datas = {
            'model': 'sale.order.line',
            'ids': ids,
            'form': self.read(cr, uid, ids, context=context),
        }

        categories = set()

        for id in ids:
            categories.add(self.browse(cr, uid, id).category_id.id)

        if len(categories) != 1:
            raise except_orm(_('Warning!'), _("You should select lines with the same category!"))

        category = categories.pop()
        result = self.pool.get('product.category').read(cr, uid, category, ['voucher_name'])
        voucher_name = result['voucher_name']
        print(voucher_name)
        return {
            'type': 'ir.actions.report.xml',
            'report_name': voucher_name,  # voucher_name
            'datas': datas,
            'nodestroy': True
        }

    _defaults = {
        'start_date': lambda s, c, u, ctx: ctx.get('start', False),
        'end_date': lambda s, c, u, ctx: ctx.get('end', False),
        'state': 'draft',
        'adults': 1,
        'price_unit_cost': float(1),
        'price_unit': float(1),
        'children': 0,
        'currency_cost_id': default_currency_cost
    }
