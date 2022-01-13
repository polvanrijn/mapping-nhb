from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path
from src.preprocess.helpers import num_to_letter, num_to_two_letters, num_to_three_letters, write_to_log
import subprocess
import os
from copy import copy

EMOTIONS = {
    'anger': 'ANG',
    'amused': 'AMU',
    'Disgust': 'DIS',
    'disgust': 'DIS',
    'Neutral': 'NEU',
    'neutral': 'NEU',
    'sleepiness': 'SLE'  # Not an emotion
}
SPEAKERS = ['bea', 'jenie', 'josh', 'sam']

REPETITION = num_to_letter(1)
INTENSITY = 'XX'
CORPUS_ABRV = 'VDB'
CORPUS = 'EmoV-DB'
FILENAME = copy(CORPUS).lower() + '.tar.gz'
FOLDER_NAME = copy(CORPUS)
ILLEGAL_CODES = ['sil', 'dup']  # Entire silences or duplicates

def build_from_path(in_dir, out_dir, num_workers=1, tqdm=lambda x: x):
    executor = ProcessPoolExecutor(max_workers=num_workers)
    futures = []
    folder = in_dir + FOLDER_NAME + '/'

    if not os.path.exists(folder):
        subprocess.call(['tar', '-zxvf', FILENAME], cwd=in_dir)
    else:
        print('Folder already exists. No need to extract the tar archive again.')
    filepaths = filepaths = [str(p) for p in Path(folder).rglob('[!\.]*0[0-9][0-9][0-9].wav')]
    filepaths = sorted(filepaths)
    for path in filepaths:
        basis_name = path.split('/')[-1][:-4]
        if basis_name.startswith('.'):
            print('Skipping hidden file: %s' % basis_name)
            continue
        split_name = basis_name.split('_')
        emotion = split_name[0]
        sentence = split_name[-1]
        # range = split_name[1:-1]
        # if isinstance(range, list):
        #     range = '-'.join(range)
        # if range in ILLEGAL_CODES or sentence in ILLEGAL_CODES:
        #     print(path)
        #     continue
        speaker_number = SPEAKERS.index(path.split('/')[-3]) + 1  # 1 ensures we start at AA
        speaker = num_to_two_letters(speaker_number)
        sentence = num_to_three_letters(int(sentence))
        emotion = EMOTIONS[emotion]

        task = partial(_process_utterance, path, out_dir, emotion, sentence, speaker)
        futures.append(executor.submit(task))
    results = [future.result() for future in tqdm(futures)]
    return [r for r in results if r is not None]


def _process_utterance(path, out_dir, emotion, sentence, speaker):
    logfile = open(out_dir + '%s_%s_%s_%s_%s_%s.log' % (CORPUS_ABRV, emotion, sentence, speaker, REPETITION, INTENSITY), 'w')

    # Downsample and only take the first channel
    out_path = out_dir + '%s_%s_%s_%s_%s_%s.wav' % (CORPUS_ABRV, emotion, sentence, speaker, REPETITION, INTENSITY)
    logfile = write_to_log(['sox', path, '-b', '16', out_path, 'remix', '1', 'rate', '16000'], logfile)

    logfile.close()
