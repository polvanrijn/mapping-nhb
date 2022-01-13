from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path
from src.preprocess.helpers import num_to_letter, num_to_two_letters, num_to_three_letters, write_to_log
import subprocess
import os
from copy import copy


EMOTIONS = {
    '01': 'NEU',
    '02': 'CAL',
    '03': 'HAP',
    '04': 'SAD',
    '05': 'ANG',
    '06': 'FER',
    '07': 'DIS',
    '08': 'SUR'
}

INTENSITIES = {
    '01': 'MI',
    '02': 'HI'
}

CORPUS_ABRV = 'RAV'
CORPUS_NAME = 'RAVDESS'
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

    filepaths = [str(p) for p in Path(folder + 'Speech/').rglob('*.wav')]
    filepaths = sorted(filepaths)

    for path in filepaths:
        split_path = path.split('/')
        basis_name = split_path[-1][:-4]
        if basis_name.startswith('.'):
            print('Skipping hidden file: %s' % basis_name)
            continue

        _, _, emotion, intensity, sentence, repetition, speaker = basis_name.split('-')

        emotion = EMOTIONS[emotion]
        intensity = INTENSITIES[intensity]
        if emotion == 'NEU':
            intensity = 'XX'

        sentence = num_to_three_letters(int(sentence))
        speaker = num_to_two_letters(int(speaker))
        repetition = num_to_letter(int(repetition))

        task = partial(_process_utterance, path, out_dir, emotion, speaker, sentence, repetition, intensity)
        futures.append(executor.submit(task))
    results = [future.result() for future in tqdm(futures)]
    return [r for r in results if r is not None]



def _process_utterance(path, out_dir, emotion, speaker, sentence, repetition, intensity):
    logfile = open(out_dir + '%s_%s_%s_%s_%s_%s.log' % (CORPUS_ABRV, emotion, sentence, speaker, repetition, intensity), 'w')

    # Downsample and only take the first channel
    out_path = out_dir + '%s_%s_%s_%s_%s_%s.wav' % (CORPUS_ABRV, emotion, sentence, speaker, repetition, intensity)
    logfile = write_to_log(['sox', path, out_path, 'remix', '1', 'rate', '16000'], logfile)

    logfile.close()
