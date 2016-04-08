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


class ResultList(TransientModel):
    _name = 'result.list'

    merge_id = fields.Many2one('base.product.merge.automatic.wizard', string=_('Wizard'), ondelete='cascade')
    similar_product_id = fields.Many2one('product.product', string=_('Similar Product'), ondelete='cascade')
    base_product_id = fields.Many2one('product.product', string=_('Base Product'))
    actual = fields.Boolean(_('Actual'), default=True)

    def check_sale_order(self, prod):
        sol = self.env['sale.order.line']
        lines = sol.search([('name', '=', prod.name_template)])
        return len(lines)

    @api.multi
    def merge(self):
        pass

    # @api.multi
    # def delete(self):
    #     obj = self[0]
    #     if self.check_sale_order(obj.similar_product_id):
    #         raise except_orm(_('Error'), _('This product belongs to a order, it can\'t be deleted'))
    #     else:
    #         pp = self.env['product.product']
    #         pt = self.env['product.product']
    #         pc = self.env['product.category']
    #         product_p = pp.search([('id', '=', obj.similar_product_id.id)])
    #         product_t = pt.search([('id', '=', obj.similar_product_id.product_tmpl_id.id)])
    #         product_c = pc.search([('id', '=', product_t.categ_id.id)])
    #         table = self.env['product.' + product_c.name.lower()]
    #         element = table.search([('product_id', '=', product_p.id)])
    #
    #         try:
    #             element.unlink()
    #             product_p.unlink()
    #             product_t.unlink()
    #             obj.unlink()
    #         except Exception as e:
    #             raise except_orm(_('Error'), _('Something went wrong!!!\n Message: ' + str(e.message)))
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         # 'flags': {'form': {'action_buttons': True}},
    #         'res_model': 'base.product.merge.automatic.wizard',
    #         'res_id': obj.merge_id.id,
    #         'context': {
    #             'values': self.env.context.get('domain', False),
    #             'obj': obj.merge_id.id
    #         }
    #     }

    @api.multi
    def unlink(self):
        if len(self):
            obj = self[0]
            if self.check_sale_order(obj.similar_product_id):
                raise except_orm(_('Error'), _('This product belongs to a order, it can\'t be deleted'))
            else:
                pp = self.env['product.product']
                pt = self.env['product.product']
                pc = self.env['product.category']
                product_p = pp.search([('id', '=', obj.similar_product_id.id)])
                product_t = pt.search([('id', '=', obj.similar_product_id.product_tmpl_id.id)])
                product_c = pc.search([('id', '=', product_t.categ_id.id)])
                table = self.env['product.' + product_c.name.lower()]
                element = table.search([('product_id', '=', product_p.id)])

                try:
                    element.unlink()
                    product_p.unlink()
                    product_t.unlink()
                except Exception as e:
                    raise except_orm(_('Error'), _('Something went wrong!!!\n Message: ' + str(e)))
        return super(ResultList, self).unlink()

    @api.multi
    def write(self, vals):
        return super(ResultList, self).write(vals)


class MergePartnerAutomaticProduct(TransientModel):
    _name = 'base.product.merge.automatic.wizard'

    base = fields.Many2one('product.product', string=_('Product'), help=_(
        "Select for find other products with similar names, leave empty for find all product similarities"))

    state = fields.Selection([('begin', 'Begin'), ('finished', 'Finished')], _('State'), default='begin', readonly=True,
                             select=True)

    result = fields.Many2one('product.product', string=_('Result'))

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
        return ratio >= 0.7

    @api.onchange('result')
    def change_result(self):
        rl = self.env['result.list']
        res = []
        for x in rl.search([('merge_id', '!=', False)]):
            x.write({
                'merge_id': False
            })
            res.append((2, x.id))
        if len(res):
            self.update({
                'list_repeated_id': res
            })
        _id = self.env.context.get('obj', False)
        res = []
        if self.result.id:
            for y in rl.search([('base_product_id', '=', self.result.id), ('actual', '=', True)]):
                y.write({
                    'merge_id': _id
                })
                res.append((1, y.id, {
                    'merge_id': _id
                }))
            if len(res):
                self.update({
                    'list_repeated_id': res
                })

    @api.multi
    def dummy_button(self):
        obj = self[0]
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            # 'flags': {'form': {'action_buttons': True}},
            'res_model': 'base.product.merge.automatic.wizard',
            'res_id': obj.id,
            'context': {
                'values': self.env.context.get('domain', False),
                'obj': obj.id
            }
        }

    @api.cr_uid_ids_context
    def write(self, cr, uid, ids, vals, context=None):
        return super(MergePartnerAutomaticProduct, self).write(cr, uid, ids, vals, context)
