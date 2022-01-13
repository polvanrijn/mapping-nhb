from itertools import compress, chain
import re
from src.collect_corpora.libs.IO import IO
from src.collect_corpora.libs.Database import Database

db = Database()
##############################################
# wos
WOS = IO.read_json('data/WOS.json')
for w in WOS:
    w['source'] = ['wos']
    w['identifier'] = "doi:" + w['DOI']
result = db.insert_many('v0-1_WOS', WOS, clear_before_insert=True)
print('Items newly inserted: %d' % len(result.inserted_ids))
WOS_DOI = [w['DOI'] for w in WOS]

##############################################
# IEEE
IEEE = IO.read_json('data/IEEE.json')
IEEE_DOI = [w['DOI'] for w in IEEE]
DOI_exists = [w['DOI'] in WOS_DOI for w in IEEE]
overlapping_DOI = list(compress(IEEE_DOI, DOI_exists))

query = {"DOI":{"$in":overlapping_DOI}}
result = db.find('v0-1_WOS', query)
# Lookup overlapping items
updated_posts = []
for old_post in result:
    idx = [i for i, x in enumerate([doi == old_post['DOI'] for doi in IEEE_DOI]) if x]
    if len(idx) != 1:
        raise ValueError('This may not happen')
    idx = idx[0]
    new_post = IEEE[idx]
    if 'author_keywords' in old_post.keys() and 'author_keywords' in new_post.keys() and isinstance(old_post['author_keywords'], list) and isinstance(new_post['author_keywords'], list):
        # This appends keywords that are not already present
        [old_post['author_keywords'].append(value) for value in new_post['author_keywords'] if value not in old_post['author_keywords']]
    else:
        old_post['author_keywords'] = new_post['author_keywords']

    old_post['IEEE_terms'] = new_post['IEEE_terms']
    old_post['INSPEC_terms'] = new_post['INSPEC_termes']
    old_post['INSPEC_terms_not_checked'] = new_post['INSPEC_termes_not_checked']
    old_post['citation_count_IEEE'] = new_post['citation_count_IEEE']
    all_keywords = [old_post[s] for s in old_post.keys() if len(re.findall('terms|keyword', s)) == 1 and isinstance(old_post[s], list)]
    all_keywords = list(chain.from_iterable(all_keywords)) # flatten list
    old_post['all_keywords'] = all_keywords
    old_post['source'].append('IEEE')
    old_post['identifier'] = "doi:" + old_post['DOI']
    updated_posts.append(old_post)

db.duplicate_collection('v0-1_WOS', 'v0-2_merge-IEEE')
print('Updated posts: %d' % len(updated_posts))

seen = set()
unique_posts = [x for x in updated_posts if x['DOI'] not in seen and not seen.add(x['DOI'])]
print('Unique posts: %d' % len(unique_posts))

# Delete old items
result = db.delete_many('v0-2_merge-IEEE', query)
print('Items deleted: %d' % result.deleted_count)

# Insert updated items
result = db.insert_many('v0-2_merge-IEEE', unique_posts)
print('Items re-inserted: %d' % len(result.inserted_ids))

# Add unique papers
new_posts = []
for idx in [i for i, x in enumerate([not d for d in DOI_exists]) if x]:
    new_post = IEEE[idx]
    new_post['INSPEC_terms_not_checked'] = new_post.pop('INSPEC_termes_not_checked')
    new_post['INSPEC_terms'] = new_post.pop('INSPEC_termes')
    all_keywords = [new_post[s] for s in new_post.keys() if
                    len(re.findall('terms|keyword', s)) == 1 and isinstance(new_post[s], list)]
    all_keywords = list(chain.from_iterable(all_keywords))  # flatten list
    new_post['all_keywords'] = all_keywords
    new_post['source'] = ['IEEE']
    new_post['identifier'] = "doi:" + new_post['DOI']
    new_posts.append(new_post)

result = db.insert_many('v0-2_merge-IEEE', new_posts)
print('Items newly inserted: %d' % len(result.inserted_ids))

#################################################################
# Pubmed
pubmed = IO.read_json('data/pubmed.json')
pubmed_DOI = [w['DOI'] for w in pubmed]
all_DOIs = list(chain.from_iterable([WOS_DOI, IEEE_DOI]))
DOI_exists = [w['DOI'] in all_DOIs for w in pubmed]

new_posts = []
for idx in [i for i, x in enumerate([not d for d in DOI_exists]) if x]:
    new_post = pubmed[idx]
    new_post['source'] = ['pubmed']
    new_post['identifier'] = "doi:" + new_post['DOI']
    new_posts.append(new_post)
db.duplicate_collection('v0-2_merge-IEEE', 'v0-3_merge-pubmed')
result = db.insert_many('v0-3_merge-pubmed', new_posts)
print('Items newly inserted: %d' % len(result.inserted_ids))


####################################################################
# Interspeech
ISCA = IO.read_json('data/ISCA.json')
ISCA_DOI = [w['doi'] for w in ISCA if 'doi' in w]
all_DOIs = list(chain.from_iterable([WOS_DOI, IEEE_DOI, pubmed_DOI]))
new_posts = []
for idx in [i for i, x in enumerate([not d for d in DOI_exists]) if x]:
    new_post = ISCA[idx]
    new_posts.append(new_post)
new_posts.extend([w for w in ISCA if 'doi' not in w])

identifiers = []
idxs = []
for idx in range(len(new_posts)):
    if 'doi' in new_posts[idx].keys():
        new_posts[idx]['DOI'] = new_posts[idx]['doi']
        del new_posts[idx]['DOI']
        new_posts[idx]['identifier'] = 'doi:' + new_posts[idx]['DOI']

    if 'identifier' not in new_posts[idx].keys():
        idxs.append(idx)
    else:
        if new_posts[idx]['identifier'] in identifiers:
            idxs.append(idx)
        else:
            identifiers.append(new_posts[idx]['identifier'])
    new_posts[idx]['source'] = ['ISCA']

for idx in reversed(idxs):
    del new_posts[idx]

IO.table([n['identifier'] for n in new_posts]).values()

db.duplicate_collection('v0-3_merge-pubmed', 'v0-4_merge-ISCA')
result = db.insert_many('v0-4_merge-ISCA', new_posts)
print('Items newly inserted: %d' % len(result.inserted_ids))

