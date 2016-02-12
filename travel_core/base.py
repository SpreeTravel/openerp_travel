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
from openerp.osv.osv import except_osv
from openerp.tools.translate import _


class res_partner(Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    @api.multi
    def set_conditions(self):
        import datetime
        if len(self):
            element = self[0]

            pool = self.env['customer.price']
            obj = pool.create({
                'pricelist': element.property_product_pricelist.id,
                'client': element.name,
                'start_date': datetime.datetime.now(),
                'end_date': datetime.datetime.now()
            })
            return {
                "name": 'Export Prices',
                "type": 'ir.actions.act_window',
                "res_model": 'customer.price',
                "view_type": 'form',
                "view_mode": 'form',
                "target": 'new',
                'res_id': obj.id
            }

    @api.multi
    def send_invitation(self):
        assert len(self) == 1, 'This option should only be used for a single id at a time.'
        obj = self[0]
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('travel_core', 'core_partner_invitation_email_template')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict()
        ctx.update({
            'default_model': 'res.partner',
            'default_res_id': obj.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    @api.one
    def get_signup_url(self):
        menu = self.env.ref('sale.menu_sale_quotations')
        action = self.env.ref('portal_sale.action_quotations_portal')
        return self.with_context(signup_valid=True)._get_signup_url_for_action(action=action.id,
                                                                               menu_id=menu.id)[self.id]

    def _get_reservations(self, cr, uid, ids, fields, args, context=None):
        result = {}
        order_line = self.pool.get('sale.order.line')
        for obj in self.browse(cr, uid, ids, context):
            result[obj.id] = []
            to_search = [('start_date', '>=', dt.datetime.today())]
            if obj.customer:
                to_search.append(('customer_id', '=', obj.id))
            elif obj.supplier:
                to_search.append(('supplier_id', '=', obj.id))
            else:
                continue
            l_ids = order_line.search(cr, uid, to_search, context=context)
            result[obj.id] = l_ids
        return result

    reservation_ids = fields.Many2many(compute=_get_reservations, method=True,
                                       relation='sale.order.line',
                                       string='Reservations')
    pax = fields.Boolean('Pax')

    # TODO: poner el campo pax tambien en el formulario de partner

    @api.model
    def create(self, vals, context=None):
        context = context or {}
        if context.get('supplier', False):
            vals['supplier'] = True
        return super(res_partner, self).create(vals)

    _sql_constraints = [
        ('name_partner_unique', 'unique (name)',
         'The name of the partner must be unique !'),
    ]


class option_type(Model):
    _name = 'option.type'
    name = fields.Char('Name', size=64, translate=True)
    code = fields.Char('Code', size=32)
    option_value_ids = fields.One2many('option.value', 'option_type_id',
                                       'Option Values')

    _sql_constraints = [
        ('code_uniq', 'unique (code)', 'The code of the option must be unique!')
    ]

    @api.multi
    def write(self, vals):
        black_list = ['sup', 'vt', 'vc', 'guide', 'tm', 'cl', 'rt', 'mp']
        if vals.get('code', False):
            for option in self:
                if option.code in black_list and vals['code'] != option.code:
                    raise except_osv(_('Validation!'), _('You can not modify the code for this option!'))
        return super(option_type, self).write(vals)

    @api.multi
    def unlink(self):
        black_list = ['sup', 'vt', 'vc', 'guide', 'tm', 'cl', 'rt', 'mp']
        delete_option_type = []
        for option in self:
            if option.code not in black_list:
                delete_option_type.append(option.id)
        if not delete_option_type:
            return False
        return super(option_type, self).unlink()


class option_value(Model):
    _name = 'option.value'

    name = fields.Char('Name', size=64, translate=True)
    code = fields.Char('Code', size=32)
    option_type_id = fields.Many2one('option.type', 'Option Type')
    load_default = fields.Boolean('Load Default')
    option_code = fields.Char(related='option_type_id.code', string='Potion Code', size=32)

    _defaults = {
        'load_default': False
    }

    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
        ids = self.search(cr, user, args)
        return self.name_get(cr, user, ids, context=context)

    def _check_load_default(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)
        if obj.load_default:
            cr.execute('SELECT id FROM option_value WHERE load_default=True and id<>%s and option_type_id=%s ',
                       (obj.id, obj.option_type_id.id,))
            if cr.fetchall():
                return False
        return True

    _constraints = [
        (_check_load_default, 'Error!\nOnly can choose one option with load default.',
         ['load_default', 'option_type_id']),
    ]

    def get_code_by_id(self, cr, uid, oid, context=None):
        return self.read(cr, uid, oid, ['code'], context)['code']

    def get_id_by_code(self, cr, uid, code, context=None):
        res = self.search(cr, uid, [('code', '=', code)], context=context)
        return res and res[0] or False


class destination(Model):
    _name = 'destination'
    code = fields.Char('Code', size=8)
    name = fields.Char('Name', size=128, required=True)
    description = fields.Text('Description')
    parent_id = fields.Many2one('destination', 'Parent')
    child_ids = fields.One2many('destination', 'parent_id', 'Children')


class destination_distance(Model):
    _name = 'destination.distance'
    origin = fields.Many2one('destinaon', 'Origin')
    target = fields.Many2one('destination', 'Target')
    distance = fields.Float('Distance')
