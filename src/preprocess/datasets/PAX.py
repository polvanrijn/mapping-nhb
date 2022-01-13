from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path
from src.preprocess.helpers import num_to_letter, num_to_two_letters, num_to_three_letters, write_to_log
import subprocess
import os
from copy import copy

EMOTIONS = {
    'ANG': 'ANG',
    'DIS': 'DIS',
    'FER': 'FER',
    'HAP': 'HAP',
    'NEU': 'NEU',
    'SAD': 'SAD',
    'SUR': 'SUR'
}

SPEAKERS = ['DF', 'MG', 'NA', 'SL']
DIGITS = [str(r) for r in range(10)]

INTENSITY = 'XX'

CORPUS_ABRV = 'PAX'
CORPUS_NAME = 'PAX'
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

        # Check for duplicates, e.g. 'DF_ANG_VX12(2)'
        if any(basis_name.endswith('(%d)' % i) for i in range(10)):
            print('Skipping duplicate file: %s' % basis_name)
            continue

        speaker, emotion, sentence = basis_name.split('_')

        sentence = sentence.replace('VX', '').replace('V', '')  # cut off `VX` or `V`
        if sentence[-1] in DIGITS:
            repetition = num_to_letter(1)
        else:
            repetition = num_to_letter(ord(sentence[-1]) - 96)
            sentence = sentence[:-1]

        sentence = int(sentence)
        if 'Nonsense' in path:
            sentence += 26**3-26**2  # add padding for nonsense sentences, so they start with Z, e.g. ZAA
        sentence = num_to_three_letters(sentence)

        speaker_number = SPEAKERS.index(speaker) + 1
        speaker = num_to_two_letters(speaker_number)

        emotion = EMOTIONS[emotion]

        task = partial(_process_utterance, path, out_dir, emotion, speaker, sentence, repetition)
        futures.append(executor.submit(task))
    results = [future.result() for future in tqdm(futures)]
    return [r for r in results if r is not None]



def _process_utterance(path, out_dir, emotion, speaker, sentence, repetition):
    logfile = open(out_dir + '%s_%s_%s_%s_%s_%s.log' % (CORPUS_ABRV, emotion, sentence, speaker, repetition, INTENSITY), 'w')

    # Downsample and only take the first channel
    out_path = out_dir + '%s_%s_%s_%s_%s_%s.wav' % (CORPUS_ABRV, emotion, sentence, speaker, repetition, INTENSITY)
    logfile = write_to_log(['sox', path, out_path, 'remix', '1', 'rate', '16000'], logfile)

    logfile.close()
