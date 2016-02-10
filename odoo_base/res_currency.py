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
import time
from openerp import models
from openerp.osv import osv
from openerp.tools.translate import _


class ResCurrency(models.Model):
    _name = 'res.currency'
    _inherit = 'res.currency'

    def _get_current_rate(self, cr, uid, ids, raise_on_no_rate=True, context=None):
        if context is None:
            context = {}
        res = {}
        rate_obj = self.pool.get('res.currency.rate')

        date = context.get('date')
        if not date:
            date = time.strftime(self.get_date_format(cr, uid))
        for id in ids:
            rate_ids = rate_obj.search(cr, uid, [('currency_id', '=', id),
                                                 ('date', '<=', date)],
                                       order='name desc', limit=1)
            if rate_ids:
                res[id] = rate_ids[0]
            elif not raise_on_no_rate:
                res[id] = 0
            else:
                currency = self.browse(cr, uid, id, context=context)
                raise osv.except_osv(_('Error!'),
                                     _("No currency rate associated for currency '%s' "
                                       "for the given period" % currency.name))
        return res

    def get_date_format(self, cr, uid):
        user = self.pool.get('res.users').browse(cr, uid, uid)
        if user.lang:
            code, name = user.lang
            lang_obj = self.pool.get('res.lang').search(cr, uid, [('code', '=', code)])
            if lang_obj:
                return lang_obj[0].date_format
        else:
            lang_obj = self.pool.get('res.lang').search(cr, uid, [('code', '=', 'en_US')])
            if lang_obj:
                return lang_obj[0].date_format
