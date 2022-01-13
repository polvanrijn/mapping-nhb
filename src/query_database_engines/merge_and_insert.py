from src.libs.IO import IO
from src.libs.Database import Database
from src.libs.Scraper import MetadataInserter
from selenium import webdriver

options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
driver = webdriver.Chrome(options=options, executable_path='/usr/local/bin/chromedriver')

data_path = 'merged_data.json'
data = IO.initialize_log(data_path, initialize_as_list=True)
metadata = MetadataInserter()


def process_log(log):
    all_identifiers = [d['old_identifier'] for d in data]
    for i in log:
        url = list(i.keys())[0]
        if url in all_identifiers:
            continue

        driver.get(url)

        item = {
            'data-availability': url,
            'data-availability-type': 'url',
            **i[url]
        }
        data.append({'old_identifier':url, **metadata.insert(item)})
        IO.write_json(data, data_path)


google_log = [{k: i} for k, i in IO.read_json('google_log.json').items() if i['accepted']]
process_log(google_log)
kaggle_log = [{k: i} for k, i in IO.read_json('kaggle_log.json').items() if i['accepted']]
process_log(kaggle_log)
driver.close()

db = Database()
db.duplicate_collection('v0-5_corpora_lists', 'v0-6_database_engines')
for item in data:
    item['status'] = db.COMPLETED_CORPUS

dois = [i['DOI'] for i in data if 'DOI' in i]
query = {"DOI":{"$in":dois}}
results = db.find('v0-6_database_engines', query)
def find_item_by_doi(doi):
    return [d for d in data if 'DOI' in d and d['DOI']==doi][0]
items = list(results)
for item in items:
    annotated_item = find_item_by_doi(item['DOI'])
    data.remove(annotated_item)
    item = {**annotated_item, **item}

result = db.delete_many('v0-6_database_engines', query)
print('Items deleted: %d' % result.deleted_count)

result = db.insert_many('v0-6_database_engines', items)
print('Items updated: %d' % len(result.inserted_ids))

result = db.insert_many('v0-6_database_engines', data)
print('Items inserted: %d' % len(result.inserted_ids))


