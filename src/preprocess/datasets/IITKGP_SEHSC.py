from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path
from src.preprocess.helpers import num_to_letter, num_to_two_letters, num_to_three_letters, write_to_log
import subprocess
import os
from copy import copy

INTENSITY = 'XX'
CORPUS_ABRV = 'SEH'
CORPUS = 'IITKGP_SEHSC'
FILENAME = copy(CORPUS).lower() + '.tar.gz'
FOLDER_NAME = copy(CORPUS)

EMOTIONS = {
    'anger': 'ANG',
    'disgust': 'DIS',
    'fear': 'FER',
    'happy': 'HAP',
    'neutral': 'NEU',
    'sadness': 'SAD',
    'sarcastic': 'SAR',  # Not an emotion
    'surprise': 'SUR'
}

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
    count = 0
    for path in filepaths:
        splitted_path = path.split('/')
        basis_name = splitted_path[-1][:-4]
        if basis_name.startswith('.'):
            print('Skipping hidden file: %s' % basis_name)
            continue
        emotion = EMOTIONS[splitted_path[-2]]
        speaker, session, emotion_sentence = basis_name.split('.')

        repetition = num_to_letter(int(session))
        speaker_number = int(speaker)
        if speaker_number == 71:
            speaker_number = 1
        speaker = num_to_two_letters(speaker_number)
        sentence = num_to_three_letters(int(emotion_sentence.split('-')[-1]))
        count += 1

        task = partial(_process_utterance, path, out_dir, emotion, sentence, speaker, repetition)
        futures.append(executor.submit(task))
    results = [future.result() for future in tqdm(futures)]
    return [r for r in results if r is not None]


def _process_utterance(path, out_dir, emotion, sentence, speaker, repetition):
    logfile = open(out_dir + '%s_%s_%s_%s_%s_%s.log' % (CORPUS_ABRV, emotion, sentence, speaker, repetition, INTENSITY), 'w')

    # Downsample and only take the first channel
    out_path = out_dir + '%s_%s_%s_%s_%s_%s.wav' % (CORPUS_ABRV, emotion, sentence, speaker, repetition, INTENSITY)
    logfile = write_to_log(['sox', path, '-b', '16', out_path, 'remix', '1', 'rate', '16000'], logfile)

    logfile.close()
