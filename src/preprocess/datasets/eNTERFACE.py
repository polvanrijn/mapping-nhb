from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path
from src.preprocess.helpers import num_to_letter, num_to_two_letters, num_to_three_letters, write_to_log
import subprocess
import os
from copy import copy

EMOTIONS = {
    'anger': 'ANG',
    'disgust': 'DIS',
    'fear': 'FER',
    'happiness': 'HAP',
    'sadness': 'SAD',
    'surprise': 'SUR'
}

REPETITION = num_to_letter(1)
INTENSITY = 'XX'
CORPUS_ABRV = 'ENT'
CORPUS = 'eNTERFACE'
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
        splitted_path = path.split('/')
        speaker, emotion, sentence, filename = splitted_path[-4:]
        if not sentence.startswith('sentence '):
            print('Skipping unsegmented file: %s (%s, %s, %s)' % (filename, speaker, emotion, sentence))
            continue
        speaker = num_to_two_letters(int(speaker[-2:]))
        sentence = num_to_three_letters(int(sentence[-1]))
        emotion = EMOTIONS[emotion]
        task = partial(_process_utterance, path, out_dir, emotion, sentence, speaker)
        futures.append(executor.submit(task))
    results = [future.result() for future in tqdm(futures)]
    return [r for r in results if r is not None]


def _process_utterance(path, out_dir, emotion, sentence, speaker):
    logfile = open(out_dir + '%s_%s_%s_%s_%s_%s.log' % (CORPUS_ABRV, emotion, sentence, speaker, REPETITION, INTENSITY), 'w')

    # Downsample and only take the first channel
    out_path = out_dir + '%s_%s_%s_%s_%s_%s.wav' % (CORPUS_ABRV, emotion, sentence, speaker, REPETITION, INTENSITY)
    logfile = write_to_log(['sox', path, out_path, 'remix', '1', 'rate', '16000'], logfile)

    logfile.close()
