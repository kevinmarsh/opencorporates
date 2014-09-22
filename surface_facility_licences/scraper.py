# -*- coding: utf-8 -*-

import json
import datetime
import turbotlib
import requests
import re

from bs4 import BeautifulSoup


def find_daily_links(soup, last_seen_ref):
    """
        Get the list of daily links, there should be the current and previous month of available links.
        There are older ones available in zip format by month.
    """
    re_target_pattern = re.compile(r".*FAC(?P<date>[0-9]{4}).HTML", re.IGNORECASE)
    day_links = []
    for link in soup.find_all("a"):
        href = link.get("href")
        interesting_link = re.match(re_target_pattern, href)
        if interesting_link:
            date_ref = interesting_link.groups()[0] + str(datetime.date.today().year)
            if date_ref > last_seen_ref:
                day_links.append((date_ref, href))

    return day_links


def get_soup(url, session=None):
    if not session:
        session = requests.Session()
    response = session.get(url)
    html = response.content
    return BeautifulSoup(html)


try:
    last_seen_ref = turbotlib.get_var("last_seen_ref")
except KeyError:
    last_seen_ref = "00-00-00"

session = requests.Session()
source_soup = get_soup("http://www.aer.ca/data-and-publications/activity-and-data/st97", session)
daily_links = find_daily_links(source_soup, last_seen_ref)

for date_ref, url in daily_links:
    data = {
        "sample_date": str(datetime.date.today()),
        "source_url": url,
        "date": datetime.datetime.strptime(date_ref, "%m%d%Y").strftime("%Y-%m-%d") # this is the date the data was released not when it was scraped
    }
    try:
        soup = get_soup(url, session)
    except Exception as e:
        # This is just to compensate for a wifi dropping constantly during pycon, can probably be removed once uploaded
        turbotlib.log(e)

    _td = soup.find(text="Licensee Name") # this is pretty fragile just searching for "Licensee Name"
    if _td:
        table =_td.find_parent("table")
    else:
        continue
    ordered_headers = []
    for tr in table.find_all("tr"):
        if not ordered_headers:
            ordered_headers = [re.sub("\s+", " ", td.text).strip() for td in tr.find_all("td")]
        else:
            for i, td in enumerate(tr.find_all("td")):
                data[ordered_headers[i]] = td.text
            print json.dumps(data)

    # save the last seen date in the turbolib variable
    turbotlib.save_var("last_seen_ref", last_seen_ref)
