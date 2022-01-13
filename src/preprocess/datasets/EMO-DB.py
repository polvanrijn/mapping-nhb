from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path
from src.preprocess.helpers import num_to_letter, num_to_two_letters, num_to_three_letters, write_to_log
import subprocess
import os
from copy import copy

EMOTIONS = {
    'A': 'FER',  # Angst
    'E': 'DIS',  # Ekel
    'F': 'HAP',  # Freude
    'L': 'BOR',  # Langeweile
    'N': 'NEU',  # Neutral
    'T': 'SAD',  # Trauer
    'W': 'ANG'   # Aerger
}

SENTENCES = ['a01', 'a02', 'a04', 'a05', 'a07', 'b01', 'b02', 'b03', 'b09', 'b10']

INTENSITY = "XX"
CORPUS_ABRV = 'EDB'
CORPUS = 'EMO-DB'
FILENAME = copy(CORPUS).lower() + '.tar.gz'
FOLDER_NAME = copy(CORPUS)

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
        basis_name = path.split('/')[-1][:-4]
        if basis_name.startswith('.'):
            print('Skipping hidden file: %s' % basis_name)
            continue
        speaker = num_to_two_letters(int(basis_name[0:2]))
        sentence = basis_name[2:5]
        sentence_number = SENTENCES.index(sentence) + 1  # Grab the index of the sentence
        sentence = num_to_three_letters(sentence_number)
        emotion = EMOTIONS[basis_name[5]]
        repetition = num_to_letter(ord(basis_name[6]) - 96)

        task = partial(_process_utterance, path, out_dir, emotion, sentence, speaker, repetition)
        futures.append(executor.submit(task))
    results = [future.result() for future in tqdm(futures)]
    return [r for r in results if r is not None]


def _process_utterance(path, out_dir, emotion, sentence, speaker, repetition):
    logfile = open(out_dir + '%s_%s_%s_%s_%s_%s.log' % (CORPUS_ABRV, emotion, sentence, speaker, repetition, INTENSITY), 'w')

    # Downsample and only take the first channel
    out_path = out_dir + '%s_%s_%s_%s_%s_%s.wav' % (CORPUS_ABRV, emotion, sentence, speaker, repetition, INTENSITY)
    logfile = write_to_log(['sox', path, out_path, 'remix', '1', 'rate', '16000'], logfile)

    logfile.close()
