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
from openerp import fields, api, exceptions
from openerp.models import Model
from openerp.exceptions import except_orm
from openerp.tools.translate import _

apis = ['best_day']


class api_model(Model):
    _name = 'api.model'

    api = fields.Char('Api', readonly=True)
    url = fields.Char(_('Api\'s Url'), readonly=True)

    user = fields.Char(_('User'))
    password = fields.Char(_('Password'))

    active = fields.Boolean(_('Active'), default=True)

    def get_class_implementation(self):
        if self.api not in apis:
            raise except_orm('Error', _('That API isn\'t well implemented'))
        try:
            module = 'travel_api_' + self.api + '.' + self.api
            module = importlib.import_module(module)
            return getattr(module, self.api)
        except:
            raise except_orm('Error', _('That API isn\'t well implemented'))
