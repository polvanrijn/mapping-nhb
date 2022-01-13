from src.libs.Database import Database
from src.libs.References import References
from src.libs.Scraper import MetadataInserter
from src.libs.IO import IO
import re
import json
from selenium import webdriver

def split_to_dict(string_val, allowed_values, separator=":"):
    if separator not in string_val:
        raise Exception
    d_split = string_val.split(separator)
    key = d_split[0]
    if key not in allowed_values:
        raise Exception
    value = separator.join(d_split[1:])
    return {key: value}

# To display the url
options = webdriver.ChromeOptions()
#options.add_experimental_option("excludeSwitches", ["enable-automation"])
#options.add_experimental_option('useAutomationExtension', False)
#options.add_argument("--window-position=4000,4000")
driver = webdriver.Chrome(options=options, executable_path='/usr/local/bin/chromedriver')


def alert(msg):
    driver.execute_script('alert(' + json.dumps(ref_print) + ')')


# To fill in the metadata
metadata = MetadataInserter()

db = Database()
DB_NAME = 'v1-database'

if db.find(DB_NAME, {}).count() == 0:
    db.duplicate_collection('v0-6_database_engines', DB_NAME)

count = db.find(DB_NAME, {'status': {'$ne': None}}).count()
num_corpora = db.find(DB_NAME, {'$or': [{'status': db.SCANNED_CORPUS}, {'status': db.COMPLETED_CORPUS}]}).count()
query = {
    "$and": [
        {"$or": [
            {"all_keywords": {'$regex': re.compile("corpus|database", re.IGNORECASE)}},
            {"title": {'$regex': re.compile("corpus|database", re.IGNORECASE)}}
        ]},
        {'status': None}
    ]
}

results = db.find(DB_NAME, query)
total = results.count() + count

log_path = 'search_log.json'
log = IO.initialize_log(log_path)

def clean_item(item):
    if '_id' in item:
        del item['_id']
    if '' in item:
        del item['']
    return item

for idx, result in enumerate(results):
    identifier = result['identifier']
    if identifier in log:
        item = log[identifier]
        db.update_one(DB_NAME, {"_id": result['_id']}, {"$set": clean_item(item)})
    else:
        ref_print = References.parse_citation(result)
        #driver.execute_script('alert(' + json.dumps(ref_print) + ')')
        print(ref_print)
        key = ''
        while key not in ['R', 'C', 'A', 'M', 'V']:

            key = input("Press R to reject, A for abstract, V to view the website, C for corpus, M for marking:").capitalize()
            update_dict = {}
            if key == 'A':
                key = ''
                if 'abstract' in result.keys():
                    print(result['abstract'])
                else:
                    print('Abstract not available')
            elif key == 'V':
                if 'DOI' in result:
                    driver.get('http://doi.org/' + result['DOI'])
                elif 'identifier' in result:
                    driver.get(list(split_to_dict(result['identifier'], ['url']).values())[0])
                else:
                    raise Exception
                key = ''
            elif key in ['R', 'C', 'M']:
                if key == 'R':
                    update_dict['status'] = db.REJECTED
                elif key == 'C':
                    #driver.get('http://doi.org/' + result['DOI'])
                    update_dict['status'] = db.SCANNED_CORPUS
                    update_dict = {**metadata.insert(result), **update_dict}
                    num_corpora += 1
                    print(IO.bold('%d corpora') % num_corpora)
                elif key == 'M':
                    update_dict['status'] = db.INTERESTING
                log[identifier] = update_dict
                IO.write_json(log, log_path)
                db.update_one(DB_NAME, {"_id": result['_id']}, {"$set": clean_item(update_dict)})
    print("\n\n%.1f%% finished, %d items to go \n\n" % ((((idx + 1 + count) / total) * 100), (total - idx - 1 - count)))
