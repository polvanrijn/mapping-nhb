import time
from math import ceil
import os
import pandas as pd
from random import random
from MAPS.a_collect_corpora.Scraper import Scraper
service = 'IEEE'

scraper = Scraper(headless=False)
for keyword1 in ['speech', 'voice', 'vocal', 'prosody']:
    for keyword2 in ['emotion*', 'affect*']:
        if keyword1 == 'speech' and keyword2 == 'emotion*':
            continue
        scraper.get("https://ieeexplore.ieee.org/search/advanced")
        time.sleep(4)
        inputs = scraper.try_xp('//form//*[contains(@class, "ng-pristine") and @type="text"]', single=False)
        # Fill in keyword 1
        inputs[0].clear()
        inputs[0].send_keys(keyword1)
        inputs[1].clear()
        inputs[1].send_keys(keyword2)
        # Search it
        scraper.execute_script("window.scrollTo(0, 1000);")
        button = scraper.try_xp('//*[contains(@class, "layout-btn-blue") and contains(./span/text(), "Search")]')
        button.click()
        time.sleep(0.5)

        def click_export():
            time.sleep(1)
            scraper.try_xp('//button/a[contains(text(), "Export")]').click()
            scraper.try_xp('//button[contains(@class, "SearchResults_Download")]').click()
            time.sleep(5)

        click_export()
        glob_path = '/Users/pol.van-rijn/Downloads/export*.csv'
        filename = scraper.wait_until_download_finished(glob_path)
        df = pd.read_csv(filename, header=0, escapechar='\\', sep=",", error_bad_lines=False)

        if not os.path.exists('data/%s' % service):
            os.mkdir('data/%s' % service)
        df.to_csv('data/%s/%s+%s_2000.csv' % (service, keyword1, keyword2))
        os.remove(filename)

        num_results = int(scraper.try_xp('//span[@class="strong"]', single=False)[1].text.replace(',', ''))
        remaining = num_results - 2000

        if remaining > 0:
            scraper.try_xp('//*[@label="Per Page"]/button').click()
            scraper.try_xp('//*[@class="filter-popover-opt-text" and text()="100"]').click()
            time.sleep(1)
            results_per_page = 100
            pages_to_scrape = ceil(remaining/results_per_page)
            total_pages = ceil(num_results/results_per_page)

            for page_idx in [total_pages - x for x in range(pages_to_scrape)]:
                current_url = scraper.current_url()
                scraper.get(current_url.split('pageNumber=')[0] + ("pageNumber=%d" % page_idx))
                pause = 2 + random() * 8
                print('wait %f seconds' % pause)
                time.sleep(pause)
                scraper.try_xp('//input[contains(@class, "results-actions-selectall-checkbox")]').click()
                click_export()
                filename = scraper.wait_until_download_finished(glob_path)
                df = pd.read_csv(filename, header=0, escapechar='\\', sep=",", error_bad_lines=False)
                df.to_csv('data/%s/%s+%s_%d.csv' % (service, keyword1, keyword2, page_idx))
                os.remove(filename)

# Read IEEE
scraper.combine_all_csv('data/IEEE/*.csv', 'data/IEEE_combined.csv')
scraper.close()