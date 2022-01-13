import pandas as pd
import math
import numpy as np
import re
from src.libs.IO import IO

IO.mkdir('data')

#########################
# Interspeech
#########################
conference_names = ["INTERSPEECH_%s" % year for year in range(2000, 2020)]
[conference_names.append("EUROSPEECH_%s" % year) for year in range(1989, 2000, 2)]
[conference_names.append("ICSLP_%s" % year) for year in range(1990, 1999, 2)]
conference_names.append("ECST_1987")

ISCA_conferences = []
for conf_name in conference_names:
    ISCA_conferences.extend(IO.read_json('../a_scrape_references/data/%s.json' % conf_name))

IO.write_json(ISCA_conferences, 'data/ISCA.json')

# WOS
# Remove NAs
WOS_df = pd.read_csv('../scrape_references/data/WOS_combined.csv')
# Skip the first row
WOS_df = WOS_df.iloc[:, 1:]
columns = []
for col in WOS_df.columns:
    na_perc = np.where(WOS_df[col].isna())[0].size/WOS_df.shape[0]
    if na_perc < 0.5:
        columns.append(col)
    print('Column %s %f' % (col, na_perc))

new_names = ['names', 'full_names', 'title', 'journal', 'language', 'publication_type', 'author_keywords', 'keywords_plus', 'abstract', 'affiliation', 'author_information', 'email', 'citation_count_WOS', 'NR', 'TC', 'wos_usage_count_180', 'wos_usage_count_2013', 'U2', 'PU', 'PI', 'PA', 'journal_cap', 'journal_abbr', 'month_day', 'year', 'volume', 'issue', 'MA', 'BP', 'DOI', 'EA', 'category1', 'category2', 'SC', 'GA', 'HP']
WOS_df.columns = new_names

cols_to_keep = ['names', 'full_names', 'title', 'journal', 'language', 'publication_type', 'author_keywords', 'keywords_plus', 'abstract', 'affiliation', 'author_information', 'email', 'citation_count_WOS',  'wos_usage_count_180', 'wos_usage_count_2013', 'journal_abbr', 'month_day', 'year', 'volume', 'issue','category1', 'category2', 'DOI']
WOS_df = WOS_df[cols_to_keep]

WOS_df = WOS_df.loc[pd.notna(WOS_df.DOI), :]
full_data = []
for idx, r in enumerate(range(WOS_df.shape[0])):
    post_data = dict(WOS_df.iloc[r, :])
    if not isinstance(post_data['full_names'], str):
        print('Skipped row %d' % idx)
        continue
    post_data['full_names'] = IO.split_names(post_data['full_names'].split(';'))
    post_data['keywords_plus'] = IO.split_keywords(post_data['keywords_plus'])
    post_data['author_keywords'] = IO.split_keywords(post_data['author_keywords'])
    post_data['category1'] = IO.split_keywords(post_data["category1"])
    post_data['category2'] = IO.split_keywords(post_data["category2"])
    for irrelevant_key in ['affiliation', 'author_information', 'email',]:
        post_data.pop(irrelevant_key, None)

    full_data.append(post_data)
    IO.print_progress_bar(idx + 1, WOS_df.shape[0], prefix = 'Progress:', suffix = 'Complete', length = 50)
IO.write_json(full_data, 'data/WOS.json')

# IEEE
IEEE_df = pd.read_csv('../scrape_references/data/IEEE_combined.csv').iloc[:, 2:]
IEEE_df = IEEE_df.loc[pd.notna(IEEE_df.DOI), :]
relevant_columns = ['Document Title', 'Authors', 'Publication Year', 'Volume', 'Issue', 'Abstract', 'DOI', 'Author Keywords', 'IEEE Terms', 'INSPEC Controlled Terms', 'INSPEC Non-Controlled Terms', 'Article Citation Count']
IEEE_df = IEEE_df[relevant_columns]
IEEE_df.columns = ['title', 'full_names', 'year', 'volume', 'issue', 'abstract', 'DOI', 'author_keywords', 'IEEE_terms', 'INSPEC_termes', 'INSPEC_termes_not_checked', 'citation_count_IEEE']
full_data = []
DOI_to_remove = []
for idx, r in enumerate(range(IEEE_df.shape[0])):
    post_data = dict(IEEE_df.iloc[r, :])
    if not isinstance(post_data['full_names'], str):
        print('Skipped row %d' % idx)
        continue

    if math.isnan(post_data['citation_count_IEEE']):
        post_data['citation_count_IEEE'] = 0
    post_data['year'] = int(post_data['year'])
    post_data['full_names'] = IO.split_names(post_data['full_names'].split('; '), split_by=' ', family_name_first = False)
    post_data['author_keywords'] = IO.split_keywords(post_data['author_keywords'], split_by=';')
    post_data['IEEE_terms'] = IO.split_keywords(post_data['IEEE_terms'], split_by=';')
    post_data['INSPEC_termes'] = IO.split_keywords(post_data['INSPEC_termes'], split_by=';')
    post_data['INSPEC_termes_not_checked'] = IO.split_keywords(post_data['INSPEC_termes_not_checked'], split_by=';')
    full_data.append(post_data)
    IO.print_progress_bar(idx + 1, IEEE_df.shape[0], prefix='Progress:', suffix='Complete', length=50)
IO.write_json(full_data, 'data/IEEE.json')


######################
# pubmed
#####################
pubmed_df = pd.read_csv('../scrape_references/data/pubmed_combined.csv').iloc[:, 1:]
pubmed_df.columns = ['title', 'url', 'full_names', 'details', 'short_details', 'resource', 'type', 'ID', 'db', 'uid', 'prop', 'yolo', 'DOI']
relevant_columns = ['full_names', 'title', 'details', 'DOI']
pubmed_df = pubmed_df[relevant_columns]
pubmed_df = pubmed_df.loc[pd.notna(pubmed_df.DOI), :]
full_data = []
for idx, r in enumerate(range(pubmed_df.shape[0])):
    post_data = dict(pubmed_df.iloc[r, :])
    if not isinstance(post_data['full_names'], str):
        print('Skipped row %d' % idx)
        continue
    post_data['full_names'] = IO.split_names(post_data['full_names'].split(', '), split_by=' ')
    if not isinstance(post_data['details'], str):
        print('Skipped row %d' % idx)
        continue
    post_data['year'] = int(re.search('[0-9]{4}', post_data['details']).group(0))
    full_data.append(post_data)
IO.write_json(full_data, 'data/pubmed.json')

