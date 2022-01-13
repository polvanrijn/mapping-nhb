import time
from random import random
import os
import datetime
from itertools import compress
import pandas as pd
from src.libs.Scraper import Scraper

data_path = 'data/%s/combined_search_%d.csv'
service = 'wos'
scraper = Scraper(headless=False)
scraper.get("https://apps.webofknowledge.com/WOS_AdvancedSearch_input.do?product=WOS&search_mode=AdvancedSearch")
scraper.try_xp('//a[text() = "Advanced Search"]').click()
time.sleep(0.5)

queries = []
for keyword1 in ['speech', 'voice', 'vocal', 'prosody']:
    for keyword2 in ['emotion*', 'affect*']:
        queries.append("TS = (%s AND %s)" % (keyword1, keyword2))

search_input = scraper.try_xp('//*[@id="value(input1)"]')
search_input.send_keys(" OR ".join(queries))
search_input.submit()

time.sleep(0.5)

scraper.try_xp('//*[@id="hitCount"]').click()
time.sleep(0.5)
# Select 50 results per page
scraper.try_xp('//*[@id="select2-selectPageSize_bottom-container"]').click()
scraper.try_xp('//*[@id="select2-selectPageSize_bottom-results"]/*[contains(@id, "-50")]').click()
time.sleep(0.5)

all_pages = list(range(1, int(scraper.try_id('pageCount.top').text) + 1))
bool_idx = [not os.path.exists(data_path % (service, page_idx)) for page_idx in all_pages]
page_idxs = list(compress(all_pages, bool_idx))
current_time = datetime.datetime.utcnow()

first_page_in_session = True
for page_idx in page_idxs:
    time.sleep(0.5)
    go_to_page = scraper.try_cls('goToPageNumber-input')
    go_to_page.clear()
    go_to_page.send_keys(page_idx)
    go_to_page.submit()

    # Pause a bit
    pause = 2 + random() * 8
    print('wait %f seconds' % pause)
    time.sleep(pause)

    try:
        # Select all
        scraper.try_xp('//*[@id="SelectPageChkId"]').click()

        # Export it
        scraper.try_xp('//*[@class="selectedExportOption"]//button').click()
        if first_page_in_session:
            scraper.try_cls('quickOutputOther').click()
            first_page_in_session = False
        # Select all fields
        scraper.try_xp('//*[@id="select2-bib_fields-container"]').click()
        scraper.try_xp('//*[@class="select2-results__option"][2]').click()
        # Select mac tab separated
        scraper.try_xp('//*[@id="select2-saveOptions-container"]').click()
        scraper.try_xp('//*[contains(@id,"tabMacUTF8")]').click()
        scraper.try_xp('//*[@id="exportButton"]').click()

        latest_file = scraper.wait_until_download_finished('/Users/pol.van-rijn/Downloads/*.txt')

        # Close
        scraper.try_xp('//*[contains(@class,"quickoutput-cancel-action")]').click()

        df = pd.read_csv(latest_file, sep='\t', error_bad_lines=False, header=0, escapechar='\\', engine='python')

        # Record content
        print('Time elapsed (page: %d): %s' % (page_idx, datetime.datetime.utcnow() - current_time))
        current_time = datetime.datetime.utcnow()
        df.to_csv(data_path % (service, page_idx))

        # Remove record
        os.remove(latest_file)
    except Exception:
        print('Something went wrong in %s on page %d' % (service, page_idx))


select_columns = ['PT', 'GP', 'CA', 'TI', 'BS', 'LA', 'HO', 'DE', 'ID', 'AB', 'C1', 'RP', 'CR', 'NR', 'TC', 'Z9', 'U1',
                  'U2', 'PU', 'PI', 'PA', 'BN', 'J9', 'JI', 'PD', 'PY', 'VL', 'MA', 'BP', 'AR', 'EA', 'PG', 'WC', 'SC',
                  'GA', 'HP']
rename_columns = ['Unnamed: 0', 'PT', 'AU', 'BA', 'BE', 'GP', 'AF', 'BF', 'CA', 'TI',
                  'SO', 'SE', 'BS', 'LA', 'DT', 'CT', 'CY', 'CL', 'SP', 'HO', 'DE',
                  'ID', 'AB', 'C1', 'RP', 'EM', 'RI', 'OI', 'FU', 'FX', 'CR', 'NR',
                  'TC', 'Z9', 'U1', 'U2', 'PU', 'PI', 'PA', 'SN', 'EI', 'BN', 'J9',
                  'JI', 'PD', 'PY', 'VL', 'IS', 'PN', 'SU', 'SI', 'MA', 'BP', 'EP',
                  'AR', 'DI', 'D2', 'EA', 'PG', 'WC', 'SC', 'GA', 'UT', 'PM', 'OA',
                  'HC', 'HP', 'DA']

scraper.combine_all_csv('data/wos/*.csv', 'data/wos_combined.csv', doi_column='AR', rename_columns=rename_columns,
                        select_columns=select_columns)
scraper.close()