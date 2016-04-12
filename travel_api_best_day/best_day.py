import requests
from lxml import etree

from openerp import models, fields
from openerp.tools.translate import _


class destinations(models.Model):
    _inherit = 'destination'

    best_day_id = fields.Char(_('Best Day ID'))


class best_day(models.Model):
    url = fields.Char(_('Url'))
    username = fields.Char(_('Username'))
    password = fields.Char(_('Password'))

    def fill_credentials(self):
        return {
            'a': self.username,
            'ip': self.password
        }

    def hotels_request(self, params):
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

    def send_request(self, _dict):
        return requests.get(self.url, params=_dict)

    def parse_countries(self, r, destinations):
        tree = etree.fromstring(r.text)
        codes = []
        for x in tree:
            tmp = destinations.search([('name', '=', x[1].text)])
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
        tree = etree.fromstring(r.text)
        codes = []
        parent = destinations.search([('best_day_id', '=', code)])
        if not (parent and parent.id):
            return
        for x in tree:
            tmp = destinations.search([('name', '=', x[1].text)])
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
                    'parent_id': parent
                })
            codes.append(x[0].text)
        return codes

    def get_destinations(self):
        params = self.fill_credentials()
        destinations = self.env['destinations']
        dsts = destinations.search([('best_day_id', '!=', False)])
        params['ic'] = None
        destin_url = 'http://testxml.e-tsw.com/AffiliateService/AffiliateService.svc/restful/GetDestinations'
        country_url = 'http://testxml.e-tsw.com/AffiliateService/AffiliateService.svc/restful/GetCountries'
        if len(dsts):
            return dsts
        else:
            r = requests.get(country_url, params=self.fill_credentials())
            codes = self.parse_countries(r, destinations)
            for code in codes:
                params['ic'] = code
                r = requests.get(destin_url, params=params)
                self.parse_cties(r, destinations, code)


def parse_countries(r):
    tree = etree.fromstring(r.text.encode('utf-8'))
    for x in tree:
        print x[0].text
        print x[1].text

        print ('--------')


b = best_day()
# b.url = 'http://testxml.e-tsw.com/AffiliateService/AffiliateService.svc/restful'
# b.username = 'MOREMEX'
# b.url = '200.55.139.220'
country_url = 'http://testxml.e-tsw.com/AffiliateService/AffiliateService.svc/restful/GetCountries'
r = requests.get(country_url, params={'a': 'MOREMEX',
                                      'ip': '200.55.139.220'
                                      })
parse_countries(r)
