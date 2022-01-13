from src.collect_corpora.libs.IO import IO
from src.collect_corpora.libs.Database import Database

filenames = ['pitterman_2010',
             'el_ayadi_2011',
             'juslin_2017',
             'lassalle_2019',
             'ververidis_2006',
             'swain_2018',
             'anagnostopoulos_2015']

data = []
identifiers = []
for filename in filenames:
    values = IO.read_json('%s/data.json' % filename)
    keys = [row['identifier'] for row in values]
    merged_data = IO.safe_merge(keys, values)
    data.append(merged_data.values())
    identifiers.append(list(merged_data.keys()))

merged_data = IO.safe_merge(IO.flatten(identifiers), IO.flatten(data))
log_path = 'data_availability_log.json'
data_avail_log = IO.initialize_log(log_path)


def filter_relevant_columns(d):
    if isinstance(d, dict):
        compared_items = ['emotions', 'identifier', 'language']
        return [d.get(key) for key in compared_items]


# Remove duplicates
for id, values in merged_data.items():
    if isinstance(values, list) and len(values):
        flat_values = []
        for v in values:
            if not isinstance(v, list):
                flat_values.append(v)
            else:
                for v2 in v:
                    flat_values.append(v2)
        stripped_duplicates = IO.remove_duplicate_dicts_from_list(flat_values, filter_relevant_columns)
        if flat_values != stripped_duplicates:
            print('%d from %d removed' % (len(values) - len(stripped_duplicates), len(values)))
            merged_data[id] = stripped_duplicates

merged_data['Neiberg2006'][0] = merged_data['Neiberg2006'][0][0]

# Add data availability
import pprint
import re

pp = pprint.PrettyPrinter()
prompt = "Select from u (url), e (email), f (url to application form) or x (no contact info) for %s (%d %%): "
count = 0
total = len(merged_data)
urls = []
for id, values in merged_data.items():
    count += 1
    is_doi = len(re.findall("10.\\d{4,9}/[-._;()/:a-z0-9A-Z]+", id)) == 1
    if is_doi:
        doi_url = '"' + 'http://doi.org/' + id + '"'
        identifier = doi_url
    else:
        identifier = id
    if id not in data_avail_log.keys():
        cached = False
        key = ''
        while key not in ['u', 'e', 'x', 'f']:
            if key.lower() == 'p':
                pp.pprint(values)
            key = input(prompt % (identifier, int(100 * count / total)))
    else:
        cached = True
        key = data_avail_log[id]['key']
        if not isinstance(merged_data[id], list):
            if 'url' in data_avail_log[id].keys():
                urls.append(data_avail_log[id]['url'])

    pub_found = True
    if key.lower() == 'u':
        url = input('Please enter the url: ')
        key = 'url:' + url
    if key.lower() == 'f':
        url = input('Please enter the url for application form: ')
        key = 'form:' + url
    elif key.lower() == 'e':
        email = input('Please enter the email address: ')
        key = 'email:' + email
    elif key.lower() == 'x':
        pub_found = False
        key = 'NO_CONTACT_INFO'

    if not cached:
        data_avail_log[id] = {}
        data_avail_log[id]['key'] = key
        if is_doi or pub_found:
            if is_doi:
                url = doi_url
            elif pub_found:
                url = input('URL to the publication of %s: ' % id)
                url = url.rstrip()
            data_avail_log[id]['url'] = url
            if isinstance(merged_data[id], list):
                merged_data[id][0]['url'] = url
            else:
                merged_data[id]['url'] = url
        IO.write_json(data_avail_log, log_path)

    if isinstance(merged_data[id], list):
        merged_data[id][0]['data_availability'] = key
    else:
        merged_data[id]['data_availability'] = key


regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"

new_items = []
old_keys = list(merged_data.keys())
for id in old_keys:
    item = merged_data[id]
    if not isinstance(item, dict):
        item = item[0]

    if item['data_availability'][:4] == 'url:':
        url = item['data_availability'][4:]
        m = re.search(regex, url)
        if m:
            item['DOI'] = m.group(1)
            item['identifier'] = 'DOI:' + item['DOI']

    if item['data_availability'] == 'NO_CONTACT_INFO' and item['data_availability'] is not None:
        continue
    else:
        metadata = item['metadata']
        del item['metadata']
        metadata = list(metadata.values())[0]

        if 'reference' not in item.keys():
            reference = {}
        elif isinstance(item['reference'], dict):
            reference = item['reference']
        else:
            raise ValueError
        item_new = {**reference, **metadata, **item}
        new_items.append(item_new)

db = Database()
existing_items = []
missing_items = []

for item in new_items:
    if 'title' in item:
        title = item['title']
        if isinstance(title, list):
            title = title[0]
    else:
        title = ''
    if '_id' in item:
        del item['_id']

    item['status'] = db.SCANNED_CORPUS

    print(title)
    result = db.find('v0-4_merge-ISCA', {
        "$or": [
            {"identifier": {'$regex': re.compile('.*' + re.escape(str(item['identifier'])) + ".*", re.IGNORECASE)}},
            {"title": {'$regex': re.compile('.*' + re.escape(str(title)) + '.*', re.IGNORECASE)}},

        ]
    })
    if result.count() == 1:
        existing_items.append({**item, **result[0]})
    else:
        missing_items.append(item)

db.duplicate_collection('v0-4_merge-ISCA', 'v0-5_corpora_lists')
seen = set()
unique_existing_items = [e for e in existing_items if e['_id'] not in seen and not seen.add(e['_id'])]

query = {"_id":{"$in": [e['_id'] for e in existing_items]}}
if not db.find('v0-5_corpora_lists', query).count() == len(unique_existing_items):
    raise ValueError

result = db.delete_many('v0-5_corpora_lists', query)
print('Items deleted: %d' % result.deleted_count)

result = db.insert_many('v0-5_corpora_lists', unique_existing_items)
print('Items updated: %d' % len(result.inserted_ids))

result = db.insert_many('v0-5_corpora_lists', missing_items)
print('Items newly inserted: %d' % len(result.inserted_ids))