import requests
from lxml import etree

from openerp import models, fields, api
from openerp.tools.translate import _
from openerp.exceptions import except_orm
import time


class destination(models.Model):
    _inherit = 'destination'

    best_day_id = fields.Char(_('Best Day ID'))


class api_best_day(models.TransientModel):
    _name = 'api.best.day'
    url = fields.Char(_('Url'))
    username = fields.Char(_('Username'))
    password = fields.Char(_('Password'))

    def fill_credentials(self):
        return {
            'a': self.username,
            'ip': self.password
        }

    @api.model
    def get_all_hotels(self, dest):
        url = 'http://testxml.e-tsw.com/AffiliateService/AffiliateService.svc/restful/GetHotelsComplete'
        params = self.fill_credentials()
        params['d'] = dest.best_day_id
        r = self.send_request(url, params)
        hotels_table = self.env['product.hotel']
        pp_table = self.env['product.product']
        pt_table = self.env['product.template']
        categ_table = self.env['product.category']
        categ = categ_table.search([('name', '=', 'Hotel')])
        ps = self.env['product.supplierinfo']
        rp = self.env['res.partner']
        text = self.encode(r)
        hotels = etree.fromstring(text)
        for hotel in hotels:
            name = hotel[1].text
            h = hotels_table.search([('hotel_name', '=', name)])
            if not (h and h.id):
                if name.lower() != 'disponible':
                    pt = pt_table.create({
                        'name': name,
                        'categ_id': categ.id
                    })
                    pp = pp_table.search([('product_tmpl_id', '=', pt.id)])
                    p = hotels_table.create({
                        'hotel_name': name,
                        'product_id': pp.id,
                        'destination': dest.id
                    })
                    partner = rp.search([('name', '=', 'Best Day')])
                    if partner and partner.id:
                        ps.create({
                            'name': partner.id,
                            'product_tmpl_id': pt.id
                        })
                    else:
                        raise except_orm('Error', _("Partner error in api implementation"))
            else:
                partner = rp.search([('name', '=', 'Best Day')])
                if partner and partner.id:
                    ps_item = ps.search(
                        [('name', '=', partner.id), ('product_tmpl_id', '=', h.product_id.product_tmpl_id.id)])
                    if not (ps_item and ps_item.id):
                        ps.create({
                            'name': partner.id,
                            'product_tmpl_id': h.product_id.product_tmpl_id.id
                        })
                else:
                    raise except_orm('Error', _("Partner error in api implementation"))

    def get_all_cars(self, dest):
        url = 'http://testxml.e-tsw.com/AffiliateService/AffiliateService.svc/restful/GetHotelsComplete'
        params = self.fill_credentials()
        params['d'] = dest.best_day_id
        r = self.send_request(url, params)
        hotels = self.env['product.hotel']
        ps = self.env['product.supplierinfo']
        rp = self.env['res.partner']
        text = self.encode(r)
        hotels = etree.fromstring(text)
        for hotel in hotels:
            name = hotel[1].text
            h = hotels.search(['hotel_name', '=', name])
            if not (h and h.id):
                hotels.create({
                    'hotel_name': name
                })
                partner = rp.search('name', '=', 'Best Day')
                if partner and partner.id:
                    p = hotels.search(['hotel_name', '=', name])
                    ps.create({
                        'name': partner.id,
                        'product_tmpl_id': p.product_id.product_tmpl_id.id
                    })
                else:
                    raise except_orm('Error', _("Partner error in api implementation"))
        return self.get_products('hotel')

    @api.model
    def get_products(self, _type, destination, api='openerp'):
        prod = self.env['product.product']
        prod_type_table = self.env['product.' + _type]
        categ_table = self.env['product.category']
        categ = categ_table.search([('name', '=', str(_type).capitalize())])
        ps = self.env['product.supplierinfo']
        rp = self.env['res.partner']
        partner = rp.search([('name', '=', 'Best Day')])
        prods = [x.product_tmpl_id.id for x in ps.search([('name', '=', partner.id)])]
        ids = [x.product_id.id for x in prod_type_table.search([('destination', '=', destination)])]
        prods = prod.search(
            [('product_tmpl_id.id', 'in', prods), ('product_tmpl_id.categ_id', '=', categ.id)])
        if api == 'openerp':
            return [y.id for y in prods if y.id in ids]
        return [x for x in prods if x.id in ids]

    def hotels_request(self, params):
        url = 'http://testxml.e-tsw.com/AffiliateService/AffiliateService.svc/restful/GetHotels'
        p = self.fill_credentials()
        p['c'] = ''
        p['sd'] = ''
        p['ed'] = ''
        p['h'] = ''
        p['rt'] = ''
        p['mp'] = ''
        p['r'] = ''
        p['d'] = ''
        p['l'] = ''
        p['hash'] = ''
        r = self.send_request(url, _dict=p)
        text = self.encode(r)

    def send_request(self, url, _dict):
        return requests.get(url, params=_dict)

    def encode(self, r):
        return r.text.encode('utf-8')

    def parse_countries(self, r, destinations):
        tree = etree.fromstring(self.encode(r))
        codes = []
        for x in tree:
            tmp = destinations.search([('name', '=', x[1].text)])
            if x[0].tag.lower() == 'id' and x[1].tag.lower() == 'name':
                if tmp and tmp.id:
                    tmp.write({
                        'name': x[1].text,
                        'best_day_id': x[0].text
                    })
                else:
                    destinations.create({
                        'name': x[1].text,
                        'best_day_id': x[0].text
                    })
            codes.append(x[0].text)
        return codes

    def parse_cities(self, r, destinations, code):
        tree = etree.fromstring(self.encode(r))
        parent = destinations.search([('best_day_id', '=', code)])
        if not (parent and parent.id):
            return
        for x in tree:
            if not x[0].text == '101':
                tmp = destinations.search([('name', '=', x[1].text)])
                if x[0].tag.lower() == 'id' and x[1].tag.lower() == 'name':
                    if tmp and tmp.id:
                        tmp.write({
                            'name': x[1].text,
                            'best_day_id': x[0].text,
                            'parent_id': parent.id
                        })
                    else:
                        destinations.create({
                            'name': x[1].text,
                            'best_day_id': x[0].text,
                            'parent_id': parent.id
                        })

    @api.model
    def get_destinations(self, name):
        params = self.fill_credentials()
        destinations = self.env['destination']
        code = name.best_day_id
        dsts = destinations.search([('best_day_id', '!=', False), ('parent_id', '=', name.id)])
        destin_url = 'http://testxml.e-tsw.com/AffiliateService/AffiliateService.svc/restful/GetDestinations'
        if len(dsts):
            return dsts
        else:
            params['ic'] = code
            r = requests.get(destin_url, params=params)
            self.parse_cities(r, destinations, code)
        dsts = destinations.search([('best_day_id', '!=', False), ('parent_id', '=', name.id)])
        return dsts

    def get_countries(self):
        country_url = 'http://testxml.e-tsw.com/AffiliateService/AffiliateService.svc/restful/GetCountries'
        params = self.fill_credentials()
        destinations = self.env['destination']
        r = requests.get(country_url, params=self.fill_credentials())
        return self.parse_countries(r, destinations)
