from urllib.request import urlopen
from lxml import etree
from tqdm import tqdm
from urllib.error import HTTPError
import pandas as pd

languages = [
    "Abkhaz", "Adyghe", "Afar", "Afrikaans", "Ainu", "Albanian_(Gheg)", "Albanian_(Tosk)", "Aleut", "Altai", "Amharic",
    "Arabic", "Aramaic_(Syriac)", "Arbanaski", "Armenian", "Armenian_(Eastern)", "Assamese", "Avar", "Azeri",
    "Balochi", "Basaa", "Bashkir", "Basque", "Belarusian", "Bemba", "Bengali", "Bihari", "Bole", "Brahui", "Brazilian",
    "Breton", "Bulgarian", "Burmese", "Burushaski", "Buryat", "Buyang", "Catalan", "Cebuano", "Chechen",
    "Chinese_(Cantonese)", "Chinese_(Mandarin)", "Chuvash", "Comorian", "Cornish", "Croatian", "Czech", "Danish",
    "Dargwa", "Dhivehi_(Maldivian)", "Digor_Ossetic", "Dizi", "Douala", "Dutch", "English", "Estonian", "Even",
    "Faroese", "Finnish", "Flemish", "French", "Frisian", "Friulian", "Fula", "Galician", "Gelao", "Georgian",
    "German", "Greek_(modern)", "Greenlandic_(Eastern)", "Greenlandic_(Western)", "Gujarati", "Gypsy_Romani", "Hausa",
    "Hebrew", "Hindi", "Hungarian", "Icelandic", "Igbo", "Indonesian", "Irish", "Iron_Ossetic", "Ishkashimi",
    "Istro-Romanian", "Italian", "Japanese", "Javanese", "Kabardino-Cherkess", "Kabylian", "Kalasha", "Kalmyk",
    "Kannada", "Karelian", "Kashmiri", "Kazakh", "Ket", "Khanti", "Khmer", "Khowar", "Kivalliq", "Komi", "Korean",
    "Kurdish", "Kurukh", "Kyrgyz", "Labrador_Inuttut", "Ladin", "Lahnda", "Lak", "Lao", "Latvian", "Letzebuergesch",
    "Lezgian", "Lithuanian", "Macedonian", "Magahi", "Malagasy", "Malayalam", "Maltese", "Mansi", "Maori", "Marathi",
    "Mari", "Marwari", "Mon", "Mongolian", "Nayi", "Nenets", "Nepali", "Norwegian_(Bokmal)", "Norwegian_(Nynorsk)",
    "Oriya", "Oromo", "Oroqen", "Pashto", "Pennsylvania_Dutch", "Persian", "Polish", "Portuguese", "Provencal",
    "Punjabi", "Romanian", "Romansch", "Russian", "Sami", "Samoan", "Sardinian_Logudorese", "Sardinian_Nuorese",
    "Sariqoli", "Schwyzerduetsch", "Scots_(Scottish English)", "Scottish_Gaelic", "Serbian", "Shan", "Sheko", "Sindhi",
    "Sinhalese", "Slovak", "Slovene", "Somali", "Spanish", "Sranan", "Swahili", "Swedish", "Tagalog", "Tahitian",
    "Tajik", "Tamasheq_(Tuareg)", "Tamil", "Tashelhit", "Tatar", "Tausug", "Telugu", "Thai", "Tibetan", "Tigrigna",
    "Tmazight_(Riffian Berber)", "Tsakonian", "Turkish", "Turkmen", "Tuvan", "Ukrainian", "Urdu", "Uyghur", "Uzbek",
    "Veps", "Vietnamese", "Vlach", "Wakhi", "Walloon", "Warji", "Waziri", "Welsh", "Wolof", "Yakut", "Yiddish",
    "Yoruba", "Yupik", "Zazaki", "Zulu"
]

replacement_dict = {
    "Digor_Ossetic": 'Ossetic_(Digor)',
    "Iron_Ossetic": 'Ossetic_(Iron)',
    'Kabardino-Cherkess': 'Kabardino_Cherkess',
    "Norwegian_(Bokmal)": 'Norwegian(bokmal)',
    "Norwegian_(Nynorsk)": 'Norwegian(nynorsk)',
    "Sardinian_Logudorese": 'Sardinian_L',
    "Sardinian_Nuorese": 'Sardinian_N',
    "Tamasheq_(Tuareg)": 'Tamasheq'
}

languages = [replacement_dict[l] if l in replacement_dict.keys() else l.replace(' ', '_') for l in languages]

visited_language_pairs = []



distances = pd.DataFrame()

for language1 in tqdm(languages):
    for language2 in languages:
        if '%s_%s' % (language1, language2) not in visited_language_pairs:
            url = 'http://www.elinguistics.net/Compare_Languages.aspx?Language1=%s&Language2=%s&Order=Calc' % (
                language1, language2)
            try:
                response = urlopen(url)
                htmlparser = etree.HTMLParser()
                tree = etree.parse(response, htmlparser)

                dist = float(tree.xpath('//font[2]/b')[0].text.replace(',', '.'))
                distances = distances.append(pd.DataFrame({
                    'language1': [language1],
                    'language2': [language2],
                    'distance': dist
                }), ignore_index=True)

                visited_language_pairs.append('%s_%s' % (language1, language2))
                visited_language_pairs.append('%s_%s' % (language2, language1))
            except HTTPError:
                print('HTTPError in %s' % url)
            except:
                print('Something else went wrong %s' % url)
    distances.to_csv('distances_sparse_elinguistics.csv')

