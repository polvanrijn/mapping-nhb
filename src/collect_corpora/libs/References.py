import os
import re
import json
from src.collect_corpora.libs.IO import IO
import math

class References:
    anystyle_path = '/usr/local/lib/ruby/gems/2.7.0/gems/anystyle-cli-1.3.0/bin/anystyle'
    cmd1 = 'export PATH=/usr/local/opt/ruby/bin:$PATH'
    cmd2 = 'export PATH=/usr/local/lib/ruby/gems/2.5.0/bin:$PATH'

    @staticmethod
    def parse_citation(result, line_breaks=True):
        if 'full_names' in result:
            out = ', '.join([r['lastname'] for r in result['full_names']])
        elif 'authors' in result:
            out = ', '.join([r for r in result['authors']])
        else:
            raise Exception()
        if 'year' in result.keys() and (isinstance(result['year'], str) or not math.isnan(result['year'])):
            out += ' (%d):' % (int(float(result['year'])))
        out += "\n" if line_breaks else " "
        if 'title' in result.keys():
            out += IO.bold(result['title'] + ".")
        out += "\n" if line_breaks else " "
        if 'journal' in result.keys() and isinstance(result['journal'], str):
            #out += IO.italic(result['journal'][0].capitalize() + result['journal'][1:].lower())
            out += result['journal'][0].capitalize() + result['journal'][1:].lower()
            out += "\n" if line_breaks else " "
        if 'all_keywords' in result.keys():
            keywords = result['all_keywords']
        else:
            keywords = IO.flatten([result[s] for s in result.keys() if
                                len(re.findall('terms|keyword', s)) == 1 and isinstance(result[s], list)])
        out += "%s: %s\n" % (IO.bold('keywords'), ', '.join(keywords))
        #out += "%s: %s\n" % ('keywords', ', '.join(keywords))
        if 'DOI' in result:
            out += "%s: %s" % (IO.bold('DOI'), 'http://doi.org/' + result['DOI'])
        #out += "%s: %s" % ('DOI', 'http://doi.org/' + result['DOI'])
        return out

    @staticmethod
    def parse(filepath):
        if not os.path.exists(filepath):
            raise FileNotFoundError(filepath + ' does not exist!')

        if os.path.basename(filepath).endswith('.txt'):
            entries_json = json.load(os.popen('%s;%s; %s parse %s' % (References.cmd1, References.cmd2, References.anystyle_path, filepath)))

        elif os.path.basename(filepath).endswith('.ris'):
            from RISparser import readris
            entries_json = []
            if os.path.exists('/tmp/snippet.txt'):
                os.remove('/tmp/snippet.txt')

            with open(filepath, 'r', encoding="utf-8") as bibliography_file:
                entries = readris(bibliography_file)
                for entry in entries:
                    if 'title' in entry.keys() and 'authors' not in entry.keys():
                        os.system('printf "%s\n" >> /tmp/snippet.txt' % entry['title'])
                    else:
                        entry['author'] = [{'literal': e} for e in entry['authors']]
                        del entry['authors']
                        entries_json.append(entry)
                for entry in json.load(os.popen('%s;%s; %s parse /tmp/snippet.txt' % (References.cmd1, References.cmd2, References.anystyle_path))):
                    entries_json.append(entry)

        for idx, entry in enumerate(entries_json):
            if 'year' in entry.keys() and 'date' in entry.keys():
                entry['date'] = entry['year']
                entries_json[idx] = entry
        return entries_json

    @staticmethod
    def lookup_authors_query(authors, year):
        and1 = {"$and": [{"author.family": author} for author in authors]}
        and2 = {"$and": [{"author.literal": {'$regex': re.compile(author, re.IGNORECASE)}} for author in authors]}

        query = {
            "$and": [
                {"$or": [and1, and2]},
                {'date': {'$regex': re.compile(year, re.IGNORECASE)}}
            ]
        }
        return query