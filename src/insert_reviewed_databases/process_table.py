from src.libs.Database import Database
from src.libs.References import References
from src.libs.Language import Language
from src.libs.Emotion import Emotion
from src.libs.Scraper import Scraper
from src.libs.IO import IO
import pandas as pd
import math

def scrape_reference_by_title(title):
    scraper = Scraper(headless=False)
    scraper.get("https://apps.webofknowledge.com/WOS_GeneralSearch_input.do")
    scraper.try_xp('//*[@id="value(input1)"]').send_keys(title)
    scraper.try_xp('//*[@id="select2-select1-container"]').click()
    scraper.try_xp('//*[@id="select2-select1-results"]/*[contains(@id, "TI")]').click()
    scraper.try_xp('//*[@id="searchCell1"]/span[1]/button').click()
    scraper.wait(0.5)
    error_msg = scraper.try_xp('//*[@id="noRecordsDiv"]/div[@class="newErrorHead"]', num_tries=1)
    if error_msg is not None:
        scraper.close()
        return False
    else:
        num_results = scraper.try_id('hitCount.top', num_tries=2)
        if num_results is not None and num_results.text == "1":
            # Scrape it!
            df = scraper.scrape_all_references_on_page('wos')
            df = scraper.extract_relevant_columns(df, 'wos')
            scraper.wait(1)
            scraper.close()
            return df
        else:
            scraper.close()
            return False

def process_table(review_name, table_filename, references_filename):
    table = pd.read_csv('%s/%s' % (review_name, table_filename), sep="\t", dtype=str)

    language_lookup = Language()
    emotion_lookup = Emotion()

    languages = IO.get_all_unique([l.split(', ') for l in table['language'].values])
    if not all([l.lower() in language_lookup.languages for l in languages]):
        unsupported_languages = IO.which(languages, [l.lower() not in language_lookup.languages for l in languages])
        raise NotImplementedError('The languages %s are not supported. Please add them in the languages.csv' % ', '.join(unsupported_languages))

    emotions = IO.get_all_unique([str(e).split(', ') for e in table['emotions'].values])

    if not all([emotion_lookup.emo_to_code(e.lower()) is not None for e in emotions]):
        raise NotImplementedError('Not all emotions are not supported. Please remove or change wrong emotions or add new emotions in emotions.csv')


    log_path = '%s/lookup_log.json' % review_name
    lookup_log = IO.initialize_log(log_path)

    if not all([required_field in table.columns for required_field in ['language', 'emotions', 'reference']]):
        raise ValueError('Table does not contain all required fields!')

    # Parse references
    references = References.parse('%s/%s' % (review_name, references_filename))
    db = Database(database_name=review_name)
    db.insert_many('references', references, clear_before_insert=True)


    items = []
    for r in range(table.shape[0]):
        # Save all data in metadata
        metadata = table.iloc[r, :].to_dict()
        item = {}
        item['metadata'] = {}
        item['metadata'][review_name] = metadata
        incomplete = False

        # Extract languages
        language = [language_lookup.lang_to_code(l) for l in metadata['language'].split(', ')]
        item['language'] = language

        # Extract emotions
        emotions = [emotion_lookup.emo_to_code(e) for e in metadata['emotions'].split(', ')]
        item['emotions'] = emotions

        # Extract identifier
        identifier = None
        split_ref = metadata['reference'].split(', ')
        authors = split_ref[:-1]
        year_suffix = split_ref[-1]

        if len(year_suffix) == 5:
            year = year_suffix[:4]
            suffix = ord(year_suffix[4]) - 97
        else:
            year = year_suffix
            suffix = 0
        pseudo_ID = (''.join(authors) + year).replace(' ', '')

        def is_valid_identifier(identifier):
            return not (identifier is None or (isinstance(identifier, float) and math.isnan(identifier)))

        # Find the identifier
        try:
            if 'identifier' in metadata.keys() and is_valid_identifier(metadata['identifier']):
                # If the identifier is already present in the table, take this one
                identifier = metadata['identifier']
            else:
                # Extract authors and year of publication


                # Look the author and year up in the references of the overview paper
                query = References().lookup_authors_query(authors, year)
                result = db.find('references', query)

                if result.count() == 0:
                    print('%s not found in reference list!' % pseudo_ID)
                elif suffix + 1 > result.count():
                    print('Suffix %d does not match number of results %s' % (suffix + 1, result.count()))
                else:
                    reference = result[suffix]

                    # Check if the DOI is already in the references of the paper
                    doi_keys = IO.which(reference.keys(), ['DOI' == r.upper() for r in reference.keys()])
                    if len(doi_keys) == 1:
                        doi_key = doi_keys[0]
                        identifier = 'DOI:' + reference[doi_key]
                    else:
                        if 'title' in reference:
                            # look the publication up locally using the title
                            local_results = db.find('references', {'title': reference['title']})

                            if local_results.count() == 1:
                                # We have the reference in the local db
                                reference = local_results[0]

                            if 'identifier' in reference.keys():
                                identifier = reference['identifier']
                            elif 'DOI' in reference.keys():
                                identifier = 'DOI:' + reference['DOI']
                            else:
                                # No DOI so far! Let's look it up in Web of Science
                                if pseudo_ID in lookup_log.keys():
                                    # If we already had this item before use the log
                                    wos_reference = lookup_log[pseudo_ID]
                                else:
                                    # Scrape the reference
                                    wos_reference = scrape_reference_by_title(reference['title'])
                                    if isinstance(wos_reference, pd.DataFrame):
                                        wos_reference = wos_reference.to_dict('r')[0]
                                        reference = wos_reference
                                    lookup_log[pseudo_ID] = wos_reference
                                    IO.write_json(lookup_log, log_path)

                                if isinstance(wos_reference, dict):
                                    if 'DOI' in wos_reference.keys():
                                        identifier = wos_reference['DOI']
                    item['reference'] = reference
        except Exception as e:
            incomplete = True

        if identifier is None or (isinstance(identifier, float) and math.isnan(identifier)):
            identifier = pseudo_ID
            print('%d: Finished %s; no identifier found' % (r, identifier))
            incomplete = True
        else:
            print('%d: Finished %s; identifier found: %s' % (r, pseudo_ID, identifier))

        item['identifier'] = identifier
        item['pseudo_identifier'] = pseudo_ID
        item['incomplete'] = incomplete
        item['source'] = review_name
        items.append(item)

    IO.write_json(items, '%s/data.json' % review_name)


process_table('pitterman_2010', 'table.csv', 'references.txt')
process_table('el_ayadi_2011', 'table.csv', 'references.txt')
process_table('juslin_2017', 'table.csv', 'references.ris')
process_table('lassalle_2019', 'table.csv', 'references.ris')
process_table('ververidis_2006', 'table.csv', 'references.txt')
process_table('swain_2018', 'table.csv', 'references.ris')
process_table('anagnostopoulos_2015', 'table.csv', 'references.ris')
