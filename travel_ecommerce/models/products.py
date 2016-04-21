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
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from openerp.tools.translate import _


class product_category(Model):
    _inherit = "product.category"
    _name = 'product.category'

    @api.multi
    def update_categories(self):
        if len(self):
            obj = self[0]
            categ_table = self.env['product.public.category']
            pt = self.env['product.template']
            categ = categ_table.search([('name', '=', obj.name)])
            if not (categ and categ.id):
                categ = categ_table.create({
                    'name': obj.name
                })
            prods = pt.search([('categ_id', '=', obj.id)])
            for x in prods:
                x.write({
                    'public_categ_ids': [(4, categ.id)]
                })
