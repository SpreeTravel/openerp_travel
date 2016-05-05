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
import importlib
import openerp
from openerp import api as api_odoo
from openerp import fields, exceptions
from openerp.models import Model
from openerp.exceptions import except_orm
from openerp.tools.translate import _

apis = ['best_day']


class api_model(Model):
    _name = 'api.model'
    _rec_name = 'api'

    api = fields.Char('Api', readonly=True)
    url = fields.Char(_('Api\'s Url'), readonly=True)

    user = fields.Char(_('User'))
    password = fields.Char(_('Password'))

    active = fields.Boolean(_('Active'), default=True)

    @api_odoo.model
    def get_class_implementation(self, api):
        # CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # sys.path.append(CURRENT_DIR)
        if not api or api not in apis:
            raise except_orm('Error', _('That API isn\'t well implemented'))
        try:
            api = str(api).replace('_', '.')
            return self.env['api.' + api]
        except Exception as e:
            raise except_orm('Error', _('That API isn\'t well implemented: ') + str(e))

    @api_odoo.model
    def change_env(self, destination_id, api, obj, categ):
        obj = self.get_class_implementation(api)
        dest_table = self.env['destination']
        dest = dest_table.search([('id', '=', destination_id)])
        method = 'get_all_' + categ + 's'

        getattr(obj.sudo(), method)(dest)

        # cache = self._cache
        # with openerp.api.Environment.manage():
        #     with openerp.registry(self.env.cr.dbname).cursor() as new_cr:
        #         new_env = api_odoo.Environment(new_cr, self.env.uid, self.env.context)
        #         getattr(obj.with_env(new_env), method)(dest)
        #         new_env.cr.commit()

    @api_odoo.multi
    def update(self):
        if len(self):
            obj = self[0]
            model = self.get_class_implementation(obj.api)
            try:
                model.get_countries()
            except Exception as e:
                raise except_orm(_('Error'), str(e))
