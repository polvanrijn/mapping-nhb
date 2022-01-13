import pandas as pd
import os
from src.libs.IO import IO

class Language:
    def __init__(self):
        language_df = pd.read_csv(os.path.dirname(__file__) + '/languages.csv', header=None)
        language_df.columns = ['language', 'code']
        self.languages = [l.lower() for l in list(language_df['language'].values)]
        self.codes = list(language_df['code'].values)
        self.code_to_lang_dict = IO.zip_together(self.codes, self.languages)
        self.lang_to_code_dict = IO.zip_together(self.languages, self.codes)

    def code_to_lang(self, code):
        return IO.lookup(code, self.code_to_lang_dict, "This language code (%s) is not in our database")

    def lang_to_code(self, language):
        return IO.lookup(language, self.lang_to_code_dict, "This language (%s) is not in our database")