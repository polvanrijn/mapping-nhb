import json
import os
import itertools
from bson import ObjectId
from collections import Counter

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

class IO:
    @staticmethod
    def write_json(dict_obj, filename):
        #j = JSONEncoder().encode(dict_obj)
        j = json.dumps(dict_obj, indent=4)
        f = open(filename, "w")
        f.write(j)
        f.close()

    @staticmethod
    def read_json(filename):
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                dict_obj = json.load(f)
            return dict_obj

    @staticmethod
    def flatten(arr_2d):
        return list(itertools.chain.from_iterable(arr_2d))

    @staticmethod
    def get_all_unique(arr_2d):
        return sorted(list(set(IO.flatten(arr_2d))))

    @staticmethod
    def clean_file(old_filepath, new_filepath):
        import os
        replacements = {
            # Tilde
            '˜a': 'ã',
            '˜A': 'Ã',
            '˜o': 'õ',
            '˜O': 'Õ',
            '˜i': '~i',
            '˜I': '~I',
            '˜n': 'ñ',

            # Accent
            'a´': 'á',
            'A´': 'Á',
            'A´ ': 'Á',
            'e´': 'é',
            'E´': 'É',
            'o´': 'ó',
            'O´': 'Ó',
            'i´': 'í',
            'I´': 'Í',
            'u´': 'ú',
            'U´': 'Ú',

            'a`': 'à',
            'A`': 'À',
            'e`': 'è',
            'E`': 'È',
            'o`': 'ò',
            'O`': 'Ò',
            'i`': 'ì',
            'I`': 'Ì',
            'u`': 'ù',
            'U`': 'Ù',

            '´ı': 'ì',

            'A˚': 'Å',

            # Umlaut
            'a¨': 'ä',
            'A¨': 'Ä',
            'o¨': 'ö',
            'O¨': 'Ö',
            'u¨': 'ü',
            'U¨': 'Ü',

            '- ': ''
        }

        sed_commands = ''
        for find, replace in replacements.items():
            sed_commands += "s/%s/%s/g; " % (find, replace)

        sed_command = "sed -e '%s' %s > %s" % (sed_commands, old_filepath, new_filepath)
        os.system(sed_command)

    @staticmethod
    def print_progress_bar(iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█', print_end="\r"):
        """
        Call in a loop to create terminal progress bar
        @params:
            iteration   - Required  : current iteration (Int)
            total       - Required  : total iterations (Int)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : positive number of decimals in percent complete (Int)
            length      - Optional  : character length of bar (Int)
            fill        - Optional  : bar fill character (Str)
            printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
        """
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filled_length = int(length * iteration // total)
        bar = fill * filled_length + '-' * (length - filled_length)
        print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end=print_end)
        # Print New Line on Complete
        if iteration == total:
            print()

    @staticmethod
    def zip_together(key, values):
        if len(set(key)) > 1:
            if len(set(key)) != len(values):
                raise ValueError('Number of keys must match values')
        return dict(zip(key, values))

    @staticmethod
    def split_names(names, split_by=', ', family_name_first=True):
        splitted_names = []
        for name in names:
            pair = name.split(split_by)
            if len(pair) == 1:
                splitted_names.append(IO.zip_together(['lastname'], pair))
            else:
                if len(pair) > 2:
                    pair = [pair[0], split_by.join(pair[1:])]
                if family_name_first:
                    splitted_names.append(IO.zip_together(['lastname', 'firstname'], pair))
                else:
                    splitted_names.append(IO.zip_together(['firstname', 'lastname'], pair))
        return splitted_names

    @staticmethod
    def lookup(key, haystack, error_msg, throw_error=False):
        key = key.lower()
        if key in haystack.keys():
            return haystack[key]
        else:
            if throw_error:
                raise NotImplementedError(error_msg % key)
            else:
                print(error_msg % key)
                return None
    @staticmethod
    def which(values, bool_idx):
        return list(itertools.compress(values, bool_idx))

    @staticmethod
    def split_keywords(value, split_by='; '):
        if isinstance(value, str):
            return value.split(split_by)
        else:
            return value

    @staticmethod
    def mkdir(path):
        if not os.path.exists(path):
            os.mkdir(path)

    @staticmethod
    def safe_merge(keys, values):
        idxs_to_remove = []
        for k, i in Counter(keys).items():
            if i > 1:
                new_data = []
                for idx in IO.which(range(len(keys)), [key == k for key in keys]):
                    new_data.append(values[idx])
                    idxs_to_remove.append(idx)
                values.append(new_data)
                keys.append(k)
        for idx in reversed(sorted(idxs_to_remove)):
            del values[idx]
            del keys[idx]
        return dict(zip(keys, values))

    @staticmethod
    def table(val_arr):
        return Counter(val_arr)

    @staticmethod
    def _default_filter_fn(values):
        return values

    @staticmethod
    def remove_duplicate_dicts_from_list(values, filter_fn = _default_filter_fn):
        return [v1 for idx, v1 in enumerate(values) if filter_fn(v1) not in [filter_fn(v2) for v2 in values[idx + 1:]]]

    @staticmethod
    def initialize_log(log_path, initialize_as_list=False):
        if os.path.exists(log_path):
            return IO.read_json(log_path)
        else:
            if initialize_as_list:
                return []
            else:
                return {}

    @staticmethod
    def italic(input_str):
        return "\x1B[3m" + input_str + "\x1B[23m"

    @staticmethod
    def bold(input_str):
        return "\033[1m" + input_str + "\033[0m"
