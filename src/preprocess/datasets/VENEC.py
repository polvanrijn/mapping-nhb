from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path
from src.preprocess.helpers import num_to_letter, num_to_two_letters, num_to_three_letters, write_to_log
import subprocess
import os

FILENAME = 'venec.tar.gz'
EMOTIONS = {
    'ang': 'ANG', # Anger
    'con': 'CON', # Contempt
    'fea': 'FER',
    'hap': 'HAP',
    'int': 'INT',
    'lus': 'LUS',
    'neu': 'NEU',
    'pri': 'PRI',
    'rel': 'REL',
    'sad': 'SAD',
    'sha': 'SHA'
}
TELL = 1
HAPPENED = 2
SENTENCE_LOOKUP = {
    'AU': {
        '1': TELL,
        '2': TELL,
        '3': HAPPENED,
        '4': HAPPENED,
        '5': TELL,
        '6': HAPPENED,
        '7': HAPPENED,
        '8': TELL,
        '9': TELL,
        '10': TELL,
        '11': TELL,
        '12': HAPPENED,
        '13': HAPPENED,
        '14': TELL,
        '15': HAPPENED,
        '16': HAPPENED,
        '17': TELL,
        '18': TELL,
        '19': HAPPENED,
        '20': HAPPENED,
    },
    'IN': {
        '1': TELL,
        '2': HAPPENED,
        '3': TELL,
        '4': TELL,
        '5': TELL,
        '6': TELL,
        '7': TELL,
        '8': HAPPENED,
        '9': HAPPENED,
        '10': HAPPENED,
        '11': HAPPENED,
        '12': TELL,
        '13': TELL,
        '14': TELL,
        '15': HAPPENED,
        '16': HAPPENED,
        '17': TELL,
        '18': HAPPENED,
        '19': HAPPENED,
        '20': HAPPENED,
    },
    'KE': {
        '1': HAPPENED,
        '2': HAPPENED,
        '3': TELL,
        '4': TELL,
        '5': TELL,
        '6': HAPPENED,
        '7': TELL,
        '8': HAPPENED,
        '9': HAPPENED,
        '10': TELL,
        '11': TELL,
        '12': HAPPENED,
        '13': HAPPENED,
        '14': HAPPENED,
        '15': TELL,
        '16': TELL,
        '17': HAPPENED,
        '18': TELL,
        '19': HAPPENED,
        '20': TELL,
    },
    'SI': {
        '1': HAPPENED,
        '2': HAPPENED,
        '3': HAPPENED,
        '4': TELL,
        '5': HAPPENED,
        '6': TELL,
        '7': TELL,
        '8': TELL,
        '9': HAPPENED,
        '10': TELL,
        '11': HAPPENED,
        '12': TELL,
        '13': TELL,
        '14': TELL,
        '15': HAPPENED,
        '16': TELL,
        '17': HAPPENED,
        '18': TELL,
        '19': HAPPENED,
        '20': HAPPENED,
    },
    'US': {
        '1': HAPPENED,
        '3': TELL,
        '5': TELL,
        '6': HAPPENED,
        '7': TELL,
        '8': HAPPENED,
        '9': TELL,
        '10': HAPPENED,
        '11': HAPPENED,
        '12': TELL,
        '13': HAPPENED,
        '14': TELL,
        '15': HAPPENED,
        '16': TELL,
        '17': HAPPENED,
        '18': TELL,
        '19': HAPPENED,
        '20': TELL,
        '21': TELL,
        '22': HAPPENED,
    }
}

CORPUS_ABRV = 'VEN'
REPETITION = num_to_letter(1)
INTENSITY = 'XX'
FOLDER_NAME = 'VENEC'


def build_from_path(in_dir, out_dir, num_workers=1, tqdm=lambda x: x):
    executor = ProcessPoolExecutor(max_workers=num_workers)
    futures = []
    folder = in_dir + FOLDER_NAME + '/'

    if not os.path.exists(folder):
        subprocess.call(['tar', '-zxvf', FILENAME], cwd=in_dir)
    else:
        print('Folder already exists. No need to extract the tar archive again.')
    filepaths = sorted([str(p) for p in Path(folder).rglob('*.wav')])
    filepaths.extend(sorted([str(p) for p in Path(folder).rglob('*.WAV')]))
    for idx, path in enumerate(filepaths):
        basis_name = os.path.basename(path)[:-4]
        if basis_name.startswith('.'):
            continue
        country, speaker_emo = basis_name.split('_')
        emo = EMOTIONS[speaker_emo[-3:]]
        speaker = speaker_emo[:-3]
        speaker_number = int(speaker)
        sentence = num_to_three_letters(SENTENCE_LOOKUP[country][speaker])

        if country == 'IN':
            speaker_number += 25
        elif country == 'KE':
            speaker_number += 50
        elif country == 'SI':
            speaker_number += 75
        elif country == 'US':
            speaker_number += 100
        speaker = num_to_two_letters(speaker_number)
        task = partial(_process_utterance, path, out_dir, emo, sentence, speaker)
        futures.append(executor.submit(task))
    results = [future.result() for future in tqdm(futures)]
    return [r for r in results if r is not None]


def _process_utterance(path, out_dir, emo_abrv, sentence, speaker):
    logfile = open(
        out_dir + '%s_%s_%s_%s_%s_%s.log' % (CORPUS_ABRV, emo_abrv, sentence, speaker, REPETITION, INTENSITY), 'w')

    # Downsample and only take the first channel
    out_path = out_dir + '%s_%s_%s_%s_%s_%s.wav' % (CORPUS_ABRV, emo_abrv, sentence, speaker, REPETITION, INTENSITY)
    logfile = write_to_log(['sox', path, '-b', '16', out_path, 'remix', '1', 'rate', '16000'], logfile)

    logfile.close()
