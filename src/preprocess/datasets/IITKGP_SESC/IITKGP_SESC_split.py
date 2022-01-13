from pathlib import Path
import subprocess
import os
import parselmouth
from parselmouth.praat import call
import numpy as np

from tqdm import tqdm

f = open("/Users/pol.van-rijn/Desktop/remaining_files.txt", "r")
filepaths = [l.replace('\n', '') for l in f.readlines()]
f.close()


def process_tg(tg, name, tg_path=None):
    if tg_path is None:
        tg_path = '/tmp/' + name + '.TextGrid'
    call(tg, "Save as short text file", tg_path)

    with open(tg_path, 'r') as f:
        lines = [l.replace('\n', '') for l in f.readlines()[12:]]
    assert len(lines) % 3 == 0  # Make sure you have 3 lines per fragment
    sentence_id = 0
    sentence_dict = {}
    for i in range(len(lines) // 3):
        start = float(lines[i * 3])
        end = float(lines[i * 3 + 1])
        label = lines[i * 3 + 2].replace('"', '')
        if label == "sounding":
            sentence_id += 1
            sentence_dict[sentence_id] = {start: start, end: end}
    return sentence_id, sentence_dict

def silence_tg(sound, db, test=True, tg_path=None, min_silence_duration=0.7):
    tg = call(sound, "To TextGrid (silences)", 100, 0, -float(db), min_silence_duration, 0.1, "silent", "sounding")
    sentence_id, sentence_dict = process_tg(tg, '%d' % db, tg_path=tg_path)

    if test:
        return sentence_id
    else:
        return sentence_id, sentence_dict

def try_n(db_start, sound, step=1, debug=False, log={}):

    for i in np.arange(step, 10 + step, step):
        db = db_start - (i + 1)

        sentence_id, sentence_dict = silence_tg(sound, db, test=False)
        log[db] = sentence_id
        # if debug:
        #     print(sentence_id)
        if sentence_id == 15:
            return False, db, log

    return True, -9, log

def closest_value(key, haystack):
    absolute_difference_function = lambda list_value : abs(list_value - key)
    return min(haystack, key=absolute_difference_function)

failed_paths = []

for path in tqdm(filepaths):
    split_path = path.split('/')
    basis_name = split_path[-1][:-4]
    if basis_name.startswith('.'):
        # print('Skipping hidden file: %s' % basis_name)
        continue

    sound = parselmouth.Sound(path)

    failed = True

    for db in [20, 30, 40, 50, 60]:
        sentence_id = silence_tg(sound, db)
        if sentence_id < 15:
            break
    db_start = db


    failed, db, _ = try_n(db_start, sound)

    log = {}
    if failed:
        failed, db, log = try_n(db_start, sound, step=0.1, log=log)

    if failed:
        db_start -= 10
        #print('Try again with %d dB' % db_start)
        failed, db, log = try_n(db_start, sound, step=0.1, log=log)


    if failed:
        failed_paths.append(path)
        closest_val = closest_value(15, log.values())

        for key, val in log.items():
            if val == closest_val:
                db = key
                #print('%d dB' % db)
                break
        print('failed\n')
    else:
        print('success %s\n' % path)

    silence_tg(sound, db, tg_path=path.replace('.wav', '.TextGrid'))


print('Fix these files:')

for p in failed_paths:
    print(p)