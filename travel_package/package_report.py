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

from openerp.osv import fields
import openerp.osv as osv
from openerp.tools.translate import _
from openerp import tools


class package_report(osv.osv.osv):
    _name = "package.report"
    _auto = False
    _description = "Package Report"

    _columns = {
        'name': fields.char(_('Name')),
        'start_date': fields.date(_('Start Date'), readonly=True),
        'end_date': fields.date(_('End Date'), readonly=True),
        'price': fields.float(_('Price'), readonly=True),
        'supplier': fields.many2one('res.partner', _('Supplier'), readonly=True)
    }
    _order = 'start_date asc'

    def _select(self):
        select_str = """
             SELECT min(p.id) as id,
             pt.name as name,
              r.start_date as start_date,
             r.end_date as end_date,
             l.name as supplier,
             p.price as price
        """
        return select_str

    def _from(self):
        from_str = """
                 product_package h join product_product pp on (pp.id=h.product_id)
                join product_template pt on (pt.id=pp.product_tmpl_id)
                 join (product_supplierinfo l join pricelist_partnerinfo p on (p.suppinfo_id=l.id)
                join product_rate r on(p.product_rate_id=r.id))
                on (pt.id=l.product_tmpl_id)
        """
        return from_str

    def _group_by(self):
        group_by_str = """
            GROUP BY
                r.start_date,
                pt.name,
                r.end_date,
                l.name,
                p.price
        """
        return group_by_str

    def init(self, cr):
        # self._table = 'pricelist_partnerinfo'

        tools.sql.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            %s
            )""" % (self._table, self._select(), self._from(), self._group_by()))

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
