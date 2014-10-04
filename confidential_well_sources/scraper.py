# -*- coding: utf-8 -*-

import codecs
import datetime
import json
import re
import requests
import turbotlib


turbotlib.log('Starting run...')

# Obscure the url from search engines since code may end up on github
source_url = codecs.decode('uggc://jjj.nre.pn/qngn/pbajryy/PbaJryy.gkg', 'rot_13')
response = requests.get(source_url, timeout=20)

# So this is a plain text file, not delineated at all, luckily they have
# a semi header which is a bunch of equal signs split apart by two columns
column_starts = []
column_names = (
    'Well Location',
    'Licence Number',
    'Licensee Code and Name',
    'Confidential Type',
    'Conf. Below Frmtn',
    'Conf. Release Date',
)

if response.status_code == 200:
    turbotlib.log('Valid response received...')
    for line in response.iter_lines():
        if not column_starts and line.startswith('==='):
            # This must be the header line, let's see how wide the columns are
            column_starts = [x.start() + 1 for x in re.finditer('\s=', line)] + [len(line)]

        elif column_starts:
            if line.startswith('===') or line.startswith('\s'):
                break  # we've reached the end of the file

            data = {
                'sample_date': str(datetime.date.today()),
                'source_url': source_url,
            }
            prev_pos = 0
            for i, column_name in enumerate(column_names):
                data[column_name] = line[prev_pos:column_starts[i]].strip()
                prev_pos = column_starts[i]
            if data['Well Location'] and data['Licence Number']:
                # Now split the 'Licensee Code and Name' value
                data['Licensee Code'], data['Licensee Name'] = data['Licensee Code and Name'].split (' ', 1)
                del data['Licensee Code and Name']

                print json.dumps(data)
else:
    raise Exception('We were unable to download the txt file, perhaps the location has moved? Try looking at http://www.aer.ca/data-and-publications/activity-and-data/confidential-well-list')
