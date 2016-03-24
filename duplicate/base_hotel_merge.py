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

    merge_id = fields.Many2one('base.hotel.merge.automatic.wizard', string=_('Wizard'), ondelete='cascade')
    base_product_id = fields.Many2one('product.hotel', string=_('Base Hotel'), required=True)
    similar_product_id = fields.Many2one('product.hotel', string=_('Similar Hotel'), required=True)


class MergePartnerAutomatic(TransientModel):
    _name = 'base.hotel.merge.automatic.wizard'

    base = fields.Many2one('product.hotel', string=_('Hotel'), required=True, help=_(
        "Select for find other hotels with similar names, leave empty for find all hotel similarities"))
    # Group by
    list_repeated = fields.One2many('result.list', 'merge_id', string=_('List Repeated'))

    @api.multi
    def find_similarities(self):
        obj = self[0]
        ph = self.env['product.hotel']

        if obj.base and obj.base.id:
            hotels = ph.search([('id', '!=', obj.base.id)])
            for h in hotels:
                if self.compare_hotels(obj.base, h, 'hotel_name'):
                    obj.list_repeated.create((0, 0, {
                        'base_product_id': obj.base.id,
                        'similar_product_id': h.id
                    }))
        else:
            base_hotels = ph.search([])
            for base in base_hotels:
                hotels = ph.search([('id', '!=', base.id)])
                for h in hotels:
                    if self.compare_hotels(base, h, 'hotel_name'):
                        obj.list_repeated.create((0, 0, {
                            'base_product_id': obj.base.id,
                            'similar_product_id': h.id
                        }))
        return {
            'type': 'ir.ui.view',
            'view_type': 'form',
            'view_mode': 'form',
            'flags': {'form': {'action_buttons': True}},
            'res_model': 'base.hotel.merge.automatic.wizard',
            'res_id': obj.id
        }

    def compare_hotels(self, base, other, field):
        base_name = getattr(base, field)
        other_name = getattr(other, field)

        _, ratio = sm.find_closers([other_name], base_name)

        return ratio >= 0.6
