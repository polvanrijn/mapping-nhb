from concurrent.futures import ProcessPoolExecutor
from functools import partial
from src.preprocess.helpers import num_to_letter, num_to_two_letters, num_to_three_letters, write_to_log
import subprocess
import os
from copy import copy
from glob import glob

EMOTIONS = {
    'Colere': 'ANG',
    'Joie': 'HAP',
    'Neutre': 'NEU',
    'Tristesse': 'SAD'
}

INTENSITY = 'XX'
CORPUS_ABRV = 'DBA'
CORPUS = 'DB_Arabic'
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
    filepaths = glob(folder + '/Locuteur*/*/*.ogg')
    filepaths = sorted(filepaths)

    for path in filepaths:
        path_split = path.split('/')
        emotion = path_split[-2]
        speaker = path_split[-3]
        speaker = num_to_two_letters(int(speaker[8:]))  # they start counting at 1000

        basis_name = path_split[-1][7:-4]
        if basis_name.startswith('.'):
            print('Skipping hidden file: %s' % basis_name)
            continue

        sentence, repetition = basis_name.split('-')
        sentence = num_to_three_letters(int(sentence))

        emotion = EMOTIONS[emotion]

        repetition = num_to_letter(int(repetition))

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
