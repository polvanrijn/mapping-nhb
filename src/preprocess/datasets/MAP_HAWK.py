from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path
from src.preprocess.helpers import num_to_letter, num_to_two_letters, num_to_three_letters, write_to_log
import subprocess
import os
from copy import copy

EMOTIONS = {
    'BS': 'ANG',
    'MN': 'CON',
    'WG': 'DIS',
    'SC': 'EMB',
    'AN': 'FER',
    'BL': 'HAP',  # KEEP THIS TYPO
    'NU': 'NEU',
    'TR': 'PRI',
    'VD': 'SAD',
    'VZ': 'SUR'
}

REPETITION = num_to_letter(1)
INTENSITY = 'XX'
SENTENCE = num_to_three_letters(1)
CORPUS_ABRV = 'HAW'
CORPUS = 'MAP_HAWK'
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

    # File format:
    # 3[emotion]{2}[speaker]{2}S[gender]{1}
    for path in filepaths:
        basis_name = path.split('/')[-1][:-4]
        if basis_name.startswith('.'):
            print('Skipping hidden file: %s' % basis_name)
            continue
        emotion = EMOTIONS[basis_name[1:3]]
        speaker = num_to_two_letters(int(basis_name[3:5]))

        task = partial(_process_utterance, path, out_dir, emotion, speaker)
        futures.append(executor.submit(task))
    results = [future.result() for future in tqdm(futures)]
    return [r for r in results if r is not None]


def _process_utterance(path, out_dir, emotion, speaker):
    logfile = open(out_dir + '%s_%s_%s_%s_%s_%s.log' % (CORPUS_ABRV, emotion, SENTENCE, speaker, REPETITION, INTENSITY), 'w')

    # Downsample and only take the first channel
    out_path = out_dir + '%s_%s_%s_%s_%s_%s.wav' % (CORPUS_ABRV, emotion, SENTENCE, speaker, REPETITION, INTENSITY)
    logfile = write_to_log(['sox', path, out_path, 'remix', '1', 'rate', '16000'], logfile)

    logfile.close()
