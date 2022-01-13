from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path
from src.preprocess.helpers import num_to_letter, num_to_two_letters, num_to_three_letters, write_to_log
import subprocess
import os

EMOTIONS = {
    'ANG': 'ANG',
    'DIS': 'DIS',
    'FEA': 'FER',
    'HAP': 'HAP',
    'NEU': 'NEU',
    'SAD': 'SAD'
}

SENTENCES = ['IEO', 'TIE', 'IOM', 'IWW', 'TAI', 'MTI', 'IWL', 'ITH', 'DFA', 'ITS', 'TSI', 'WSI']

CORPUS_ABRV = 'CRE'
FILENAME = 'crema-d.tar.gz'
FOLDER_NAME = 'CREMA-D/AudioWAV'
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
        speaker, sentence, emotion, intensity = basis_name.split('_')

        speaker = num_to_two_letters(int(speaker) - 1000)  # they start counting at 1000
        sentence_number = SENTENCES.index(sentence) + 1  # Grab the index of the sentence
        sentence = num_to_three_letters(sentence_number)

        emotion = EMOTIONS[emotion]

        if intensity in ['LO', 'HI']:
            # Leave as it is
            pass
        elif intensity == 'MD':
            intensity = 'MI'
        else:
            intensity = 'XX'

        if emotion == 'NEU':
            intensity = 'XX'

        task = partial(_process_utterance, path, out_dir, emotion, sentence, speaker, intensity)
        futures.append(executor.submit(task))
    results = [future.result() for future in tqdm(futures)]
    return [r for r in results if r is not None]


def _process_utterance(path, out_dir, emotion, sentence, speaker, intensity):
    logfile = open(out_dir + '%s_%s_%s_%s_%s_%s.log' % (CORPUS_ABRV, emotion, sentence, speaker, REPETITION, intensity), 'w')

    # Downsample and only take the first channel
    out_path = out_dir + '%s_%s_%s_%s_%s_%s.wav' % (CORPUS_ABRV, emotion, sentence, speaker, REPETITION, intensity)
    logfile = write_to_log(['sox', path, out_path, 'remix', '1', 'rate', '16000'], logfile)

    logfile.close()
