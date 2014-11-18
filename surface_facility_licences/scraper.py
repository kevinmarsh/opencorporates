# -*- coding: utf-8 -*-

import codecs
import datetime
import json
import re
import requests
import turbotlib

from bs4 import BeautifulSoup


def find_daily_links(soup, last_seen_ref):
    '''
        Get the list of daily links, there should be the current and previous month of available links.
        There are older ones available in zip format by month.
    '''
    turbotlib.log('Getting daily links')
    re_target_pattern = re.compile(r'.*FAC(?P<date>[0-9]{4}).HTML', re.IGNORECASE)
    re_year_pattern = re.compile(r'[a-z]+ ([0-9]{4})$', re.IGNORECASE)
    day_links = []
    for table in soup.find_all('table', {'class': 'telerik-reTable-1'}):
        table_header = table.find_next('td')
        try:
            # Blah, a nasty hack to get the year since it looks like they reuse URLs yearly
            year = re.match(re_year_pattern, table_header.string).groups()[0]
        except AttributeError:
            # This must be the day of week table
            continue
        for link in table.find_all('a'):
            href = link.get('href')
            interesting_link = re.match(re_target_pattern, href)
            if interesting_link:
                date_ref = year + interesting_link.groups()[0]
                if date_ref > last_seen_ref:
                    day_links.append((date_ref, href))

    turbotlib.log('There are %s links to check' % len(day_links))
    return day_links


def get_soup(url, session=None):
    turbotlib.log('Fetching %s' % url)
    if not session:
        session = requests.Session()
    response = session.get(url)
    html = response.content
    return BeautifulSoup(html)


try:
    last_seen_ref = turbotlib.get_var('last_seen_ref')
    turbotlib.log('last_seen_ref: ' + last_seen_ref)
except KeyError:
    turbotlib.log('Unknown last_seen_ref, start from the beginning')
    last_seen_ref = '00000000'


source_url = codecs.decode('uggc://jjj.nre.pn/qngn-naq-choyvpngvbaf/npgvivgl-naq-qngn/fg97', 'rot_13')
session = requests.Session()
source_soup = get_soup(source_url, session)
daily_links = find_daily_links(source_soup, last_seen_ref)

for date_ref, url in daily_links:
    data = {
        'sample_date': str(datetime.date.today()),
        'source_url': url,
        'date': datetime.datetime.strptime(date_ref, '%Y%m%d').strftime('%Y-%m-%d')  # this is the date the data was released not when it was scraped
    }
    soup = get_soup(url, session)

    _td = soup.find(text='Licensee Name')  # this is pretty fragile just searching for 'Licensee Name'
    if _td:
        table = _td.find_parent('table')
    else:
        continue
    ordered_headers = []
    for tr in table.find_all('tr'):
        if not ordered_headers:
            ordered_headers = [re.sub('\s+', ' ', td.text).strip() for td in tr.find_all('td')]
        else:
            for i, td in enumerate(tr.find_all('td')):
                data[ordered_headers[i]] = td.text
            print json.dumps(data)

    # save the last seen date in the turbolib variable
    turbotlib.save_var('last_seen_ref', date_ref)
