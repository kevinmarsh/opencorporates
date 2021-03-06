# -*- coding: utf-8 -*-

import codecs
import datetime
import json
import requests
import turbotlib

from bs4 import BeautifulSoup

turbotlib.log('Starting run...')

def get_soup(url, session=None):
    if not session:
        session = requests.Session()
    turbotlib.log('Getting soup for %s' % url)
    response = session.get(url)
    html = response.content
    return BeautifulSoup(html)

session = requests.Session()
sample_date = str(datetime.date.today())
base_url ='http://www.knf.gov.pl'

# This is the first page in about 20~ paginated tables
# Obscure the url from search engines since code may end up on github
target_url = codecs.decode('uggc://jjj.xas.tbi.cy/cbqzvbgl/svaqVaQrgnvy.npgvba?pglcr=Onaxv+fc%P3%O3%P5%82qmvrypmr&nwnk=gehr&enaqbz=0.20882477751001716&co.fgneg=0', 'rot_13')
while target_url:
    soup = get_soup(target_url, session)
    for tr in soup.find_all('tr')[1:]:
        data = {
            'sample_date': sample_date,
            'source_url': target_url
        }

        for column, td in zip(('id','name','contact'), tr.find_all('td')):
            data[column] = td.text.strip()

        data['id'] = int(data['id'])

        # Now split the contact into address, telephone and fax number
        contact = [line.strip() for line in data['contact'].split('\n') if line.strip()]
        for key in ('fax', 'telephone',):
            data[key] = contact.pop().replace(('%s: ' % key[:3]), '') if ('%s: ' % key[:3]) in data['contact'] else None
        data['address'] = ', '.join(contact)

        # and get rid of the surperflous 'contact' field
        del data['contact']

        print json.dumps(data)

    # The next target is the polish word for 'next' in the pagination
    target_url_a = soup.find(text=u'następna').parent
    target_url = None if u'inactive' in target_url_a.attrs['class'] else (base_url + target_url_a.attrs['href'])
