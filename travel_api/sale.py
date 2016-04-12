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
from openerp import fields, api, exceptions
from openerp.models import Model
from openerp.exceptions import except_orm
from openerp.tools.translate import _


class sale_order(Model):
    _name = 'sale.order'
    _inherit = 'sale.order'

    api_model_id = fields.Many2one('api.model', _('API'))

    destination_id = fields.Many2one('destinations', _('Destination'))

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
                          uom=False, qty_uos=0, uos=False, name='', partner_id=False,
                          lang=False, update_tax=True, date_order=False, packaging=False,
                          fiscal_position=False, flag=False, context=None):
        if self.api_model_id.api == 'local':
            return super(sale_order, self).product_id_change(cr, uid, ids, pricelist, product, qty, uom, qty_uos, uos,
                                                             name, partner_id, lang, update_tax, date_order, packaging,
                                                             fiscal_position, flag, context)
        else:
            obj = self.api_model_id.get_class_implementation()
            pass


class res_partner(Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    api_model = fields.Boolean(_('Is API?'), default=False)
