from concurrent.futures import ProcessPoolExecutor
from functools import partial
from src.preprocess.helpers import num_to_letter, num_to_two_letters, num_to_three_letters, write_to_log
import subprocess
import os
from copy import copy
import pandas as pd
import numpy as np

EMOTIONS = {
    'anger': 'ANG',
    'joy': 'HAP',
    'neutral': 'NEU',
    'sadness': 'SAD'
}

INTENSITY = 'XX'
CORPUS_ABRV = 'EEK'
CORPUS = 'EEKK'
FILENAME = copy(CORPUS).lower() + '.tar.gz'
FOLDER_NAME = copy(CORPUS)
REPETITION = num_to_letter(1)

def build_from_path(in_dir, out_dir, num_workers=1, tqdm=lambda x: x):
    executor = ProcessPoolExecutor(max_workers=num_workers)
    futures = []
    folder = in_dir + FOLDER_NAME + '/'

    if not os.path.exists(folder):
        subprocess.call(['tar', '-zxvf', FILENAME], cwd=in_dir)
    else:
        print('Folder already exists. No need to extract the tar archive again.')

    df = pd.read_csv(folder + 'meta.csv')
    unique_sentences, sentences = np.unique(df.sentence, return_inverse=True)
    df['sentence_num'] = sentences
    for r in range(df.shape[0]):
        row = df.iloc[r,:]
        path = os.path.join(folder, row.rated_emotion, str(row.id) + '.wav')
        if 'Marju' in row['title']:
            speaker = num_to_two_letters(1)
        else:
            speaker = num_to_two_letters(2)
        sentence = num_to_three_letters(row.sentence_num)

        task = partial(_process_utterance, path, out_dir, EMOTIONS[row.rated_emotion], sentence, speaker)
        futures.append(executor.submit(task))
    results = [future.result() for future in tqdm(futures)]
    return [r for r in results if r is not None]


def _process_utterance(path, out_dir, emotion, sentence, speaker):
    logfile = open(out_dir + '%s_%s_%s_%s_%s_%s.log' % (CORPUS_ABRV, emotion, sentence, speaker, REPETITION, INTENSITY),
                   'w')

    # Downsample and only take the first channel
    out_path = out_dir + '%s_%s_%s_%s_%s_%s.wav' % (CORPUS_ABRV, emotion, sentence, speaker, REPETITION, INTENSITY)
    logfile = write_to_log(['sox', path, out_path, 'remix', '1', 'rate', '16000'], logfile)

    logfile.close()
