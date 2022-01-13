import time
import os
import bibtexparser
from src.collect_corpora.libs.Scraper import Scraper
from src.collect_corpora.libs.IO import IO


def scrape_isca(scraper, old_design, service, year, base_url):
    scraper.get(base_url)
    items = []
    a_xp = '//a' if old_design else '//a[@class="w3-text"]'
    elems = scraper.try_xp(a_xp, single=False)
    links = [elem.get_attribute('href') for elem in elems]
    links = [link for link in list(set(links)) if link is not None and link.endswith('.html')]
    links = list(set(links))
    for link in links:
        try:
            scraper.get(link)
            time.sleep(0.5)
            title_xp = '//center/h2|//center/font/h2' if old_design else '//h3'
            title = scraper.try_xp(title_xp).get_attribute('innerText')
            bib_tex = None if old_design else scraper.try_xp('//pre', single=False)[-1]
            use_bib_parser = True
            if bib_tex is None:
                use_bib_parser = False
            else:
                bib_tex_str = bib_tex.get_attribute('innerText')
                # This is soooooo ugly, but it works
                with open('bibtex.bib', 'w') as bibfile:
                    bibfile.write(bib_tex_str)
                with open('bibtex.bib') as bibtex_file:
                    bib_database = bibtexparser.load(bibtex_file)
                os.remove('bibtex.bib')

                if bib_database is not None and isinstance(bib_database.entries, list) and len(
                        bib_database.entries) == 1:
                    reference = bib_database.entries[0]
                else:
                    use_bib_parser = False

            if not use_bib_parser:
                reference = {}
                reference['title'] = title
                author_xp = '//center/h3|//center/font/h3' if old_design else '//h4'
                reference['authors'] = scraper.try_xp(author_xp).get_attribute('innerText').split(', ')
            pdf_urls = [elem.get_attribute('href') for elem in scraper.try_xp('//a', single=False) if
                        elem.get_attribute('href').endswith('.pdf')]

            if len(pdf_urls) == 1:
                reference['identifier'] = 'url:%s' % pdf_urls[0]
            if old_design:
                scraper.execute_script("document.getElementsByTagName('center')[0].remove()")
                if base_url == 'https://www.isca-speech.org/archive/icslp_2000/index.html':
                    scraper.execute_script(
                        "[... document.getElementsByTagName('p')].forEach(function(entry) {entry.remove();})")
                    abstract_p = scraper.try_xp('//body', single=False)
                else:
                    abstract_p = scraper.try_xp('//p', single=False)
            else:
                abstract_p = scraper.try_xp('//div[@class="w3-container"]/p[not(@class)]', single=False)
            reference['abstract'] = ' '.join([p.get_attribute('innerText') for p in abstract_p])
            reference['source'] = "%s_%s" % (service, year)
            items.append(reference)
            print('Finished %s (%s)' % (title, year))
        except:
            print('Something went wrong in %s' % link)
    IO.write_json(items, "data/%s_%s.json" % (service, year))

service = 'INTERSPEECH'
scraper = Scraper(headless=False)
for year in list(range(2000, 2020)):
    if os.path.exists("data/%s_%s.json" % (service, year)):
        continue

    old_design = year <= 2015
    if old_design:
        if year == 2000:
            base_url = 'https://www.isca-speech.org/archive/icslp_2000/index.html'
        elif year == 2001:
            base_url = 'https://www.isca-speech.org/archive/eurospeech_2001/index.html'
        elif year == 2002:
            base_url = 'https://www.isca-speech.org/archive/icslp_2002/index.html'
        elif year == 2003:
            base_url = 'https://www.isca-speech.org/archive/eurospeech_2003/index.html'
        else:
            base_url = 'https://www.isca-speech.org/archive/interspeech_%s/index.html' % year
    else:
        base_url = 'https://www.isca-speech.org/archive/Interspeech_%s/' % year

    scrape_isca(scraper, old_design, service, year, base_url)

old_design = True
service = 'EUROSPEECH'
for year in [1989, 1991, 1993, 1995, 1997, 1999]:
    base_url = 'https://www.isca-speech.org/archive/eurospeech_%s/index.html' % year
    scrape_isca(scraper, old_design, service, year, base_url)

service = 'ICSLP'
for year in [1990, 1992, 1994, 1996, 1998]:
    base_url = 'https://www.isca-speech.org/archive/eurospeech_%s/index.html' % year
    scrape_isca(scraper, old_design, service, year, base_url)

service = 'ECST'
year = 1987
base_url = 'https://www.isca-speech.org/archive/ecst_1987/index.html'
scrape_isca(scraper, old_design, service, year, base_url)