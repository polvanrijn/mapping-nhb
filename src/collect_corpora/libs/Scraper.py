import os
import time
import glob
import pandas as pd
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
import json

class Scraper:
    def __init__(self, first_page_in_session=True, headless=True):
        self.first_page_in_session = first_page_in_session

        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('headless')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        self.driver = webdriver.Chrome(options=options, executable_path='/usr/local/bin/chromedriver')

    # def __del__(self):
    #     try:
    #         self.driver.close()
    #     finally:
    #         ''

    # Helper functions for selecting xpath, classes and IDs
    def try_sel(self, selector, type, single, num_tries=10, wait_dur = 1):
        tries = 0
        while True:
            tries += 1
            try:
                if type == 'XP':
                    if single:
                        return self.driver.find_element_by_xpath(selector)
                    else:
                        return self.driver.find_elements_by_xpath(selector)
                elif type == 'C':
                    if single:
                        return self.driver.find_element_by_class_name(selector)
                    else:
                        return self.driver.find_elements_by_class_name(selector)
                elif type == 'ID':
                    if single:
                        return self.driver.find_element_by_id(selector)
                    else:
                        return self.driver.find_elements_by_id(selector)
            except Exception:
                print('%f sec pause' % wait_dur)
                time.sleep(wait_dur)
            if tries > num_tries:
                break

    def try_xp(self, xpath, single=True, num_tries=10, wait_dur = 1):
        return self.try_sel(xpath, 'XP', single, num_tries, wait_dur)

    def try_cls(self, class_name, single=True, num_tries=10, wait_dur = 1):
        return self.try_sel(class_name, 'C', single, num_tries, wait_dur)

    def try_id(self, ID, single=True, num_tries=10, wait_dur = 1):
        return self.try_sel(ID, 'ID', single, num_tries, wait_dur)

    def get(self, url):
        self.driver.get(url)

    def execute_script(self, script):
        self.driver.execute_script(script)

    def current_url(self):
        return self.driver.current_url

    def close(self):
        self.driver.close()
        #self.__del__()

    @staticmethod
    def wait(duration):
        time.sleep(duration)

    @staticmethod
    def wait_until_download_finished(glob_path):
        while len(glob.glob(glob_path)) == 0:
            print('Wait another 5 secs')
            time.sleep(2)
        time.sleep(0.5)
        list_of_files = glob.glob(glob_path)  # * means all if need specific format then *.csv
        return (max(list_of_files, key=os.path.getctime))

    @staticmethod
    def combine_all_csv(folder_path, new_file_path, doi_column='DOI', rename_columns=None, select_columns=None, print_progress=True):
        files = glob.glob(folder_path)
        df = pd.DataFrame()
        for filename in files:
            sub_df = pd.read_csv(filename)

            # Optionally rename columns
            if isinstance(rename_columns, list):
                if len(rename_columns) != len(sub_df.columns):
                    raise IndexError('You must specifiy a name for each column!')
                else:
                    sub_df.columns = rename_columns

            # Optionally only select specific columns
            if all([col in sub_df.columns for col in select_columns]):
                sub_df = sub_df[select_columns]
            else:
                raise ValueError('You can only filter by columns that are already in the data frame.')

            df = df.append(sub_df)

            if print_progress:
                print('Finished %s' % filename)
        df = df.loc[pd.notna(df[doi_column]), :]
        df = df.drop_duplicates(subset=doi_column, ignore_index=True)
        df.to_csv(new_file_path)

    def scrape_all_references_on_page(self, service, save_path=None):
        if service == 'wos':
            # Select all
            self.try_xp('//*[@id="SelectPageChkId"]').click()

            # Export it
            self.try_xp('//*[@class="selectedExportOption"]//button').click()
            if self.first_page_in_session:
                self.try_cls('quickOutputOther').click()
                self.first_page_in_session = False
            # Select all fields
            self.try_xp('//*[@id="select2-bib_fields-container"]').click()
            self.try_xp('//*[@class="select2-results__option"][2]').click()
            # Select mac tab separated
            self.try_xp('//*[@id="select2-saveOptions-container"]').click()
            self.try_xp('//*[contains(@id,"tabMacUTF8")]').click()
            self.try_xp('//*[@id="exportButton"]').click()

            glob_path = '/Users/pol.van-rijn/Downloads/*.txt'
            while len(glob.glob(glob_path)) == 0:
                print('Wait another 5 secs')
                time.sleep(2)
            time.sleep(0.5)
            list_of_files = glob.glob(glob_path)  # * means all if need specific format then *.csv
            latest_file = max(list_of_files, key=os.path.getctime)

            # Close
            self.try_xp('//*[contains(@class,"quickoutput-cancel-action")]').click()

            # Record content
            df = pd.read_csv(latest_file, sep='\t')

            # Remove record
            os.remove(latest_file)

            if save_path is not None:
                df.to_csv(save_path)
            else:
                return df

    def extract_relevant_columns(self, df, service):
        if service == 'wos':
            columns = ['PT', 'GP', 'CA', 'TI', 'BS', 'LA', 'HO', 'DE', 'ID', 'AB', 'C1', 'RP', 'CR', 'NR', 'TC', 'Z9', 'U1', 'U2', 'PU', 'PI', 'PA', 'BN', 'J9', 'JI', 'PD', 'PY', 'VL', 'MA', 'BP', 'AR', 'EA', 'PG', 'WC', 'SC', 'GA', 'HP']
            if not all([c in df.keys() for c in columns]):
                raise ValueError('Wrong df')

            df = df[columns]
            new_names = ['names', 'full_names', 'title', 'journal', 'language', 'publication_type', 'author_keywords',
                         'keywords_plus', 'abstract', 'affiliation', 'author_information', 'email',
                         'citation_count_WOS', 'NR', 'TC', 'wos_usage_count_180', 'wos_usage_count_2013', 'U2', 'PU',
                         'PI', 'PA', 'journal_cap', 'journal_abbr', 'month_day', 'year', 'volume', 'issue', 'MA', 'BP',
                         'DOI', 'EA', 'category1', 'category2', 'SC', 'GA', 'HP']
            df.columns = new_names

            cols_to_keep = ['names', 'full_names', 'title', 'journal', 'language', 'publication_type',
                            'author_keywords', 'keywords_plus', 'abstract', 'affiliation', 'author_information',
                            'email', 'citation_count_WOS', 'wos_usage_count_180', 'wos_usage_count_2013',
                            'journal_abbr', 'month_day', 'year', 'volume', 'issue', 'category1', 'category2', 'DOI']
            return(df[cols_to_keep])

import subprocess
class MetadataInserter():
    INFINITE_TIME_OUT  = 999999999999
    def __init__(self):
        self.scraper = Scraper(headless=False)
        self.pro = subprocess.Popen(["python", "-m", "http.server"],
                               cwd='/'.join(os.path.realpath(__file__).split('/')[:-1]))
    def __del__(self):
        self.pro.kill()
        self.scraper.close()

    def fill_in(self, id, value):
        element = self.scraper.try_id(id, num_tries=0, wait_dur=0.1)
        if element.get_attribute('type') in ['text', 'number']:
            element.send_keys(value)
        elif element.get_attribute('type') in ['select-one', 'select']:
            self.scraper.try_xp("//select[@id='%s']/option[text()='%s']" % (id, value)).click()
        elif element.get_attribute('type') == 'select-multiple':
            self.scraper.execute_script("$('#emotion').selectpicker('val', %s);" % str(value))

    def get_data(self):
        inputs = self.scraper.try_xp('//input|//select', single=False)
        data = {}
        for input in inputs:
            key = input.get_attribute('id')
            if input.get_attribute('type') in ['text', 'number']:
                value = input.get_attribute('value')
            elif input.get_attribute('type') in ['select-one', 'select']:
                value = input.get_attribute('value')
            elif input.get_attribute('type') == 'select-multiple':
                value = self.scraper.driver.execute_script("return $('#%s').val();" % key)
            else:
                value = ''
            if value != '':
                data[key] = value
        return data

    def insert(self, item = None):
        time.sleep(2)
        self.scraper.get('http://0.0.0.0:8000/fetch_meta_data.html')
        meta_data = []
        if item is not None and isinstance(item, dict):
            for id, value in item.items():
                if id == '_id':
                    continue
                try:
                    self.fill_in(id, value)
                except:
                    print('Id %s with value %s not on page' % (id, value))
                    meta_data.append({id:value})
        if len(meta_data) > 0:
            self.scraper.execute_script("$('#metadata').html(JSON.stringify(%s, null, 2))" % json.dumps(meta_data))
        WebDriverWait(self.scraper.driver, self.INFINITE_TIME_OUT).until(ec.visibility_of_element_located((By.CLASS_NAME, "finished")))
        data = self.get_data()

        return data