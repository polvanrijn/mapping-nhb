from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path
from src.preprocess.helpers import num_to_letter, num_to_two_letters, num_to_three_letters, write_to_log
import subprocess
import os
from copy import copy

EMOTIONS = {
    'a': 'ANG',
    'd': 'DIS',
    'f': 'FER',
    'h': 'HAP',
    'n': 'NEU',
    'sa': 'SAD',
    'su': 'SUR'
}

SPEAKERS = ['DC', 'JE', 'JK', 'KL']

REPETITION = num_to_letter(1)
INTENSITY = 'XX'
CORPUS_ABRV = 'SAV'
CORPUS_NAME = 'SAVEE'
FILENAME = copy(CORPUS_NAME).lower() + '.tar.gz'
FOLDER_NAME = CORPUS_NAME

def build_from_path(in_dir, out_dir, num_workers=1, tqdm=lambda x: x):
    executor = ProcessPoolExecutor(max_workers=num_workers)
    futures = []
    folder = in_dir + FOLDER_NAME + '/'

    if not os.path.exists(folder):
        subprocess.call(['tar', '-zxvf', FILENAME], cwd=in_dir)
    else:
        print('Folder already exists. No need to extract the tar archive again.')

    filepaths = [str(p) for p in Path(folder).rglob('*.wav')]
    filepaths = sorted(filepaths)

    for path in filepaths:
        split_path = path.split('/')
        basis_name = split_path[-1][:-4]
        if basis_name.startswith('.'):
            print('Skipping hidden file: %s' % basis_name)
            continue

        speaker_number = SPEAKERS.index(split_path[-2]) + 1
        speaker = num_to_two_letters(speaker_number)

        sentence_str = basis_name[-2:]
        sentence = num_to_three_letters(int(sentence_str))
        emotion = EMOTIONS[copy(basis_name).replace(sentence_str, '')]


        task = partial(_process_utterance, path, out_dir, emotion, speaker, sentence)
        futures.append(executor.submit(task))
    results = [future.result() for future in tqdm(futures)]
    return [r for r in results if r is not None]



def _process_utterance(path, out_dir, emotion, speaker, sentence):
    logfile = open(out_dir + '%s_%s_%s_%s_%s_%s.log' % (CORPUS_ABRV, emotion, sentence, speaker, REPETITION, INTENSITY), 'w')

    # Downsample and only take the first channel
    out_path = out_dir + '%s_%s_%s_%s_%s_%s.wav' % (CORPUS_ABRV, emotion, sentence, speaker, REPETITION, INTENSITY)
    logfile = write_to_log(['sox', path, out_path, 'remix', '1', 'rate', '16000'], logfile)

    logfile.close()
