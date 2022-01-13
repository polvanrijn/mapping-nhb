from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path
from src.preprocess.helpers import num_to_letter, num_to_two_letters, num_to_three_letters, write_to_log
import subprocess
import os
from copy import copy

CORPUS_ABRV = 'J01'
CORPUS = 'JUSLIN_LAUKKA_2001'
FILENAME = copy(CORPUS).lower() + '.tar.gz'
FOLDER_NAME = copy(CORPUS)

EMOTIONS = {
    'an': 'ANG',
    'di': 'DIS',
    'fe': 'FER',
    'ha': 'HAP',
    'ne': 'NEU',
    'sa': 'SAD'
}

INTENSITIES = {
    's': 'HI',
    'm': 'LO',
    'e': 'MI'
}

SENTENCES = ['q', 's']
REPETITION = num_to_letter(1)

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
        basis_name = basis_name.replace('noex', 'ne')
        speaker, remaining = basis_name.split('_')
        sentence_number = SENTENCES.index(remaining[1])
        sentence = num_to_three_letters(sentence_number)

        print(remaining)
        print(remaining[2:4])
        emotion = EMOTIONS[remaining[2:4]]

        speaker = num_to_two_letters(int(speaker))

        intensity = INTENSITIES[remaining[-1]]

        task = partial(_process_utterance, path, out_dir, emotion, sentence, speaker, intensity)
        futures.append(executor.submit(task))
    results = [future.result() for future in tqdm(futures)]
    return [r for r in results if r is not None]


def _process_utterance(path, out_dir, emotion, sentence, speaker, intensity):
    logfile = open(out_dir + '%s_%s_%s_%s_%s_%s.log' % (CORPUS_ABRV, emotion, sentence, speaker, REPETITION, intensity),
                   'w')

    # Downsample and only take the first channel
    out_path = out_dir + '%s_%s_%s_%s_%s_%s.wav' % (CORPUS_ABRV, emotion, sentence, speaker, REPETITION, intensity)
    logfile = write_to_log(['sox', path, out_path, 'remix', '1', 'rate', '16000'], logfile)

    logfile.close()
