from pathlib import Path
import textgrids
import subprocess
import os
from MAPS.b_preprocess.helpers import num_to_letter, num_to_two_letters, num_to_three_letters
import parselmouth
from parselmouth.praat import call
import numpy as np

from tqdm import tqdm

folder = '/Volumes/Files/Corpora/Corpora/Emotional corpus/Accepted/intended/IITKGP_SESC/'
new_folder = '/Volumes/Files/Corpora/Corpora/Emotional corpus/Accepted/intended/IITKGP_SESC/automatically_split/'

if not os.path.exists(new_folder):
    os.mkdir(new_folder)
INTENSITY = 'XX'
CORPUS_ABRV = 'SES'
CORPUS = 'IITKGP_SESC'
EMOTIONS = {
    'Anger': 'ANG',
    'Angerl': 'ANG', # typo in the naming
    'Compassion': 'COM',
    'Compasion': 'COM', # typo in the naming
    'Compasssion': 'COM', # typo in the naming
    'Disgust': 'DIS',
    'Fear': 'FER',
    'Happy': 'HAP',
    'Neutral': 'NEU',
    'Sarcastic': 'SAR',  # Not an emotion
    'Surprise': 'SUR'
}

def check_textgrid(tg_path):
    tg = textgrids.TextGrid(tg_path)
    if not sum([1 if i.text =='sounding' else 0 for i in tg['silences']]) == 15:
        print('Check %s' % tg_path)

def split_audio(tg_path, repetition, speaker, emotion):
    tg = textgrids.TextGrid(tg_path)
    t1s = [i.xmin for i in tg['silences'] if i.text =='sounding']
    t2s = [i.xmax for i in tg['silences'] if i.text =='sounding']

    wav_path = tg_path.replace('.TextGrid', '.wav')

    for idx in range(len(t1s)):
        t1 = t1s[idx]
        dur = t2s[idx] - t1

        sentence = num_to_three_letters(idx)
        out_path = new_folder + '%s_%s_%s_%s_%s_%s.wav' % (CORPUS_ABRV, emotion, sentence, speaker, repetition, INTENSITY)
        subprocess.call(['sox', wav_path, out_path, 'remix', '1', 'rate', '16000', 'trim', str(t1), str(dur)])

filepaths = [str(p) for p in Path(folder).rglob('*.TextGrid')]
filepaths = sorted(filepaths)
for path in filepaths:
    splitted_path = path.split('/')
    basis_name = splitted_path[-1].split('.')[0]
    if basis_name.startswith('.'):
        print('Skipping hidden file: %s' % basis_name)
        continue
    speaker = num_to_two_letters(int(splitted_path[-3].replace('Speaker (', '').replace(')', '')))
    repetition = num_to_letter(int(splitted_path[-2].replace('Season (', '').replace(')', '')))

    emotion = EMOTIONS[basis_name.replace('_all', '')]
    split_audio(path, repetition, speaker, emotion)
    #check_textgrid(f)
