from concurrent.futures import ProcessPoolExecutor
from functools import partial
from glob import glob
from src.preprocess.helpers import num_to_letter, num_to_two_letters, num_to_three_letters, write_to_log
import subprocess
import os, time
from copy import copy

EMOTIONS = {
    'ang': 'ANG',
    'dis': 'DIS',
    'fea': 'FER',
    'hap': 'HAP',
    'neu': 'NEU',
    'sad': 'SAD',
    'sur': 'SUR'
}

REPETITIONS = {
    'blk 1': 1,
    'blk 2': 2,
    'blk 4': 3,
    'blk 5': 4
}

SENTENCE = num_to_three_letters(1)

CORPUS_ABRV = 'DAF'
CORPUS_NAME = 'DaFEX'
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
    filepaths = glob(folder+ 'data/Actor*/[B,b][l]ock[1-2, 4-5]/*.avi')
    filepaths = sorted(filepaths)

    for path in filepaths:
        basis_name = path.split('/')[-1][:-4]
        if basis_name.startswith('.'):
            print('Skipping hidden file: %s' % basis_name)
            continue
        speaker, repetition, emotion, intensity = basis_name.split(' - ')

        speaker = num_to_two_letters(int(speaker.replace('act ', '')))  # Each actor starts with `act `
        emotion = EMOTIONS[emotion]
        repetition = REPETITIONS[repetition]

        if emotion == 'NEU':
            local_repetition = int(intensity[0])
            repetition = (repetition-1)*3 + local_repetition
            intensity = 'XX'
        else:
            if intensity in ['LO', 'HI']:
                # Leave as it is
                pass
            elif intensity == 'MD':
                intensity = 'MI'
            else:
                intensity = 'XX'
        repetition = num_to_letter(repetition)
        task = partial(_process_utterance, path, out_dir, emotion, speaker, intensity, repetition)
        futures.append(executor.submit(task))
    results = [future.result() for future in tqdm(futures)]
    return [r for r in results if r is not None]



def _process_utterance(path, out_dir, emotion, speaker, intensity, repetition):
    logfile = open(out_dir + '%s_%s_%s_%s_%s_%s.log' % (CORPUS_ABRV, emotion, SENTENCE, speaker, repetition, intensity), 'w')

    # Convert movie to sound
    tmp_path = out_dir + '%s_%s_%s_%s_%s_%s_tmp.wav' % (CORPUS_ABRV, emotion, SENTENCE, speaker, repetition, intensity)
    subprocess.call(['ffmpeg', '-y', '-i', path, tmp_path], stdout=logfile, stderr=subprocess.STDOUT)

    # Downsample and only take the first channel
    out_path = out_dir + '%s_%s_%s_%s_%s_%s.wav' % (CORPUS_ABRV, emotion, SENTENCE, speaker, repetition, intensity)
    time.sleep(0.1)
    subprocess.call(['sox', tmp_path, out_path, 'remix', '1', 'rate', '16000'], stdout=logfile, stderr=subprocess.STDOUT)
    time.sleep(0.1)
    subprocess.call(['rm', '-f', tmp_path], stdout=logfile, stderr=subprocess.STDOUT)

    logfile.close()
