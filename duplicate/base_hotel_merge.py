# -*- coding: latin1 -*-
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

import xlrd
from openerp.exceptions import except_orm
from openerp import api, fields
from openerp.models import TransientModel, Model
from openerp.tools.translate import _
import stringmatcher as sm
import os


class travel_hotel(Model):
    _name = 'travel.hotel'

    id = fields.Integer('Id', readonly=True)
    create_date = fields.Datetime('Create Date', readonly=True)


class ResultList(TransientModel):
    _name = 'result.list'

    merge_id = fields.Many2one('base.product.merge.automatic.wizard', string=_('Wizard'), ondelete='cascade')
    similar_product_id = fields.Many2one('product.product', string=_('Similar Product'), required=True)
    base_product_id = fields.Many2one('product.product', string=_('Base Product'))
    actual = fields.Boolean(_('Actual'), default=True)

    @api.multi
    def merge(self):
        pass

    @api.multi
    def delete(self):
        pass


class MergePartnerAutomaticProduct(TransientModel):
    _name = 'base.product.merge.automatic.wizard'

    base = fields.Many2one('product.product', string=_('Product'), help=_(
        "Select for find other products with similar names, leave empty for find all product similarities"))

    state = fields.Selection([('begin', 'Begin'),
                              ('finished', 'Finished')],
                             _('State'),
                             default='begin',
                             readonly=True,
                             select=True)

    result = fields.Many2one('product.product', string=_('Product\'s Result'))

    # Group by
    list_repeated_id = fields.One2many('result.list', 'merge_id', string=_('List Repeated'))

    def reset_rl(self, rl):
        for x in rl.search([('actual', '=', True)]):
            x.write({
                'actual': False
            })

    @api.multi
    def find_similarities(self):
        obj = self[0]
        ph = self.env['product.product']
        rl = self.env['result.list']
        self.reset_rl(rl)
        domain = []
        b = None
        old_results = rl.search([('merge_id', '=', obj.id)])
        if len(old_results):
            for r in old_results:
                r.write({
                    'merge_id': False
                })
        if obj.base and obj.base.id:
            b = obj.base
            hotels = ph.search([('id', '!=', obj.base.id)])
            copy = False
            for h in hotels:
                if self.compare_hotels(obj.base, h, 'name_template'):
                    copy = True
                    rl.create({
                        'merge_id': obj.id,
                        'similar_product_id': h.id,
                        'base_product_id': obj.base.id
                    })
            if copy:
                rl.create({
                    'merge_id': obj.id,
                    'similar_product_id': obj.base.id,
                    'base_product_id': obj.base.id
                })
        else:
            base_hotels = ph.search([])
            first = True
            for base in base_hotels:
                copy = False
                hotels = ph.search([('id', '!=', base.id)])
                for h in hotels:
                    if self.compare_hotels(base, h, 'name_template'):
                        copy = True
                        rl.create({
                            'similar_product_id': h.id,
                            'base_product_id': base.id
                        })
                        if first:
                            b = base
                            first = False
                if copy:
                    domain.append(base.id)
                    rl.create({
                        'similar_product_id': base.id,
                        'base_product_id': base.id
                    })
        if b:
            for x in rl.search([('base_product_id', '=', b.id), ('actual', '=', True)]):
                x.write({
                    'merge_id': obj.id
                })
        obj.write({
            'state': 'finished',
            'result': b.id if b else False
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            # 'flags': {'form': {'action_buttons': True}},
            'res_model': 'base.product.merge.automatic.wizard',
            'res_id': obj.id,
            'context': {
                'values': domain,
                'obj': obj.id
            }
        }

    def compare_hotels(self, base, other, field):
        base_name = getattr(base, field)
        other_name = getattr(other, field)
        _, ratio = sm.find_closers([other_name], base_name)
        return ratio >= 0.6

    @api.onchange('result')
    def change_result(self):
        rl = self.env['result.list']
        for x in rl.search([('merge_id', '!=', False)]):
            x.write({
                'merge_id': False
            })
        _id = self.env.context.get('obj', False)
        for y in rl.search([('base_product_id', '=', self.result.id), ('actual', '=', True)]):
            y.write({
                'merge_id': _id
            })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'base.product.merge.automatic.wizard',
            'res_id': _id,
            'context': {
                'values': self.env.context.get('domain', False),
                'obj': _id
            }
        }
