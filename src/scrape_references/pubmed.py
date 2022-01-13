import time
import os
import pandas as pd
import re
from src.libs.Scraper import Scraper

service = 'pubmed'
scraper = Scraper(headless=False)
for keyword1 in ['speech', 'voice', 'vocal', 'prosody']:
    for keyword2 in ['emotion', 'affect']:
        scraper.get("https://www.ncbi.nlm.nih.gov/pubmed/advanced?")

        search_form = scraper.try_id('fv_0')
        search_form.send_keys(keyword1)

        search_form = scraper.try_id('fv_1')
        search_form.send_keys(keyword2)
        scraper.try_xp('//*[@id="search"]').click()

        time.sleep(0.5)
        scraper.try_xp('//*[@id="sendto"]/a').click()
        time.sleep(0.5)
        scraper.try_xp('//*[@id="dest_File"]').click()
        time.sleep(0.5)
        scraper.try_xp('//*[@id="file_format"]/option[text()="CSV"]').click()
        time.sleep(0.5)
        scraper.try_xp('//*[@id="submenu_File"]/button').click()

        latest_file = scraper.wait_until_download_finished('/Users/pol.van-rijn/Downloads/*.csv')
        df = pd.read_csv(latest_file, quotechar='"', sep=",")
        dois = []
        for row in df.Description:
            doi_result = re.search('doi: (.*)(\. |\.$)', row)

            if doi_result:
                dois.append(doi_result.group(1).split('. ')[0])
            else:
                dois.append('')

        df['doi'] = dois
        df.to_csv('data/%s/%s+%s.csv' % (service, keyword1, keyword2))

        print('Finished: %s, %s+%s' % (service, keyword1, keyword2))
        os.remove(latest_file)

scraper.combine_all_csv('data/pubmed/*.csv', 'data/pubmed_combined.csv', doi_column='doi')