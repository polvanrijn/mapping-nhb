import os
import pandas as pd
import re
from src.collect_corpora.libs.Scraper import Scraper
from src.collect_corpora.libs.IO import IO

# Clean up references
references_file = os.getcwd() + '/references_uncorrected.txt'
new_references_file = os.getcwd() + '/../references.txt'
IO.clean_file(references_file, new_references_file)

# Setup scraper
scraper = Scraper()
scraper.get('file:///' + os.getcwd() + '/table.html')

sections = scraper.try_xp('//div[contains(@class, "WordSection")]', single=False)
df = pd.DataFrame()
for idx, section in enumerate(sections):
    item = {}
    # Clean txt
    txt = section.text.replace('- ', '').replace('\n', '')

    # Keys
    regex = '<[A-Z]+>'
    txt_split = re.split(regex, txt)
    txt_split = [t.lstrip().rstrip() for t in txt_split]

    if not ':' in txt_split[0]:
        raise ValueError()
    first_row_split = txt_split[0].split(':')
    language = first_row_split[0].lstrip().rstrip()
    language = [l.lstrip().rstrip() for l in language.split(',')]
    description = first_row_split[1].lstrip().rstrip()
    txt_split = txt_split[1:]
    txt_split.insert(0, language)
    txt_split.insert(1, description)

    pattern = re.compile(regex)
    keys = re.findall(pattern, txt)
    keys = [k[1:-1].lower() for k in keys]
    keys.insert(0, 'language')
    keys.insert(1, 'description')

    if len(keys) != len(txt_split):
        raise ValueError()

    metadata = dict(zip(keys, txt_split))
    df = df.append(pd.DataFrame(metadata), ignore_index=True)

df.to_csv('../table.csv', index=False)