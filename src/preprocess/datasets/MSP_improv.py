from concurrent.futures import ProcessPoolExecutor
from functools import partial
from glob import glob
from src.preprocess.helpers import num_to_letter, num_to_two_letters, num_to_three_letters, write_to_log
import subprocess
import os

EMOTIONS = {
    'A': 'ANG',
    'H': 'HAP',
    'N': 'NEU',
    'S': 'SAD'
}

count_repetitions = {}

INTENSITY = 'XX'

CORPUS_ABRV = 'IMP'
CORPUS_NAME = 'MSP improv'
FILENAME = 'msp_improv.tar.gz'
FOLDER_NAME = CORPUS_NAME

def build_from_path(in_dir, out_dir, num_workers=1, tqdm=lambda x: x):
    executor = ProcessPoolExecutor(max_workers=num_workers)
    futures = []
    folder = in_dir + FOLDER_NAME + '/'

    if not os.path.exists(folder):
        subprocess.call(['tar', '-zxvf', FILENAME], cwd=in_dir)
    else:
        print('Folder already exists. No need to extract the tar archive again.')

    # This corpus is kinda special. It consists of dyadic interactions between two speakers
    # - Recordings of the preparations (P) --> not relevant
    # - The utterance of the target sentence (R) --> relevant
    # - Recordings of Improvised scene turns (S) --> no annotation, so we skip it
    # - improvised utterance of the same sentence (T) --> relevant

    filepaths = glob(folder + 'audio/session*/session*/*/[R, T]/*.wav')
    filepaths = sorted(filepaths)

    for path in filepaths:
        split_path = path.split('/')
        basis_name = split_path[-1][:-4]
        if basis_name.startswith('.'):
            print('Skipping hidden file: %s' % basis_name)
            continue

        _, _, sentence_emotion, speaker, task, listener_speaker_turn = basis_name.split('-')

        # Speaker format [M|F][session]
        speaker_number = (int(speaker[-2:])-1) * 2
        if speaker[0] == 'M':
            speaker_number += 1
        elif speaker[0] == 'F':
            speaker_number += 2
        else:
            raise NotImplementedError('Male is coded as uneven numbers, female as even numbers')
        speaker = num_to_two_letters(speaker_number)

        # Create repetitions
        key = sentence_emotion + speaker
        if key in count_repetitions.keys():
            count_repetitions[key] += 1
        else:
            count_repetitions[key] = 1
        repetition = num_to_letter(count_repetitions[key])

        emotion = EMOTIONS[sentence_emotion[-1]]
        sentence = num_to_three_letters(int(sentence_emotion[1:3]))
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
