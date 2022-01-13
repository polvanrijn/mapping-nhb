from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path
from src.preprocess.helpers import num_to_letter, num_to_two_letters, num_to_three_letters, write_to_log
import subprocess
import os
FILENAME = 'ahoemo2.tar.gz'
EMOTIONS = {
    'anger': 'ANG',
    'disgust': 'DIS',
    'fear': 'FER',
    'happiness': 'HAP',
    'neutral': 'NEU',
    'sadness': 'SAD',
    'surprise': 'SUR'
}
CORPUS_ABRV = 'AH2'
REPETITION = num_to_letter(1)
INTENSITY = 'XX'
FOLDER_NAME = 'ahoemo2'

def build_from_path(in_dir, out_dir, num_workers=1, tqdm=lambda x: x):
    executor = ProcessPoolExecutor(max_workers=num_workers)
    futures = []
    folder = in_dir + FOLDER_NAME + '/'

    if not os.path.exists(folder):
        subprocess.call(['tar', '-zxvf', FILENAME], cwd=in_dir)
    else:
        print('Folder already exists. No need to extract the tar archive again.')
    for speaker_count, gender in enumerate(['male', 'female']):
        for emotion, emo_abrv in EMOTIONS.items():
            print(gender + ' ' + emotion)
            filepaths = [str(p) for p in Path(folder + '%s/wav/%s/' % (gender, emotion)).rglob('*.wav')]
            filepaths = sorted(filepaths)

            for idx, path in enumerate(filepaths):
                sentence = num_to_three_letters(idx + 1)
                speaker = num_to_two_letters(speaker_count + 1)
                task = partial(_process_utterance, path, out_dir, emo_abrv, sentence, speaker)
                futures.append(executor.submit(task))
            results = [future.result() for future in tqdm(futures)]
    return [r for r in results if r is not None]



def _process_utterance(path, out_dir, emo_abrv, sentence, speaker):
    logfile = open(out_dir + '%s_%s_%s_%s_%s_%s.log' % (CORPUS_ABRV, emo_abrv, sentence, speaker, REPETITION, INTENSITY), 'w')

    # Downsample and only take the first channel
    out_path = out_dir + '%s_%s_%s_%s_%s_%s.wav' % (CORPUS_ABRV, emo_abrv, sentence, speaker, REPETITION, INTENSITY)
    logfile = write_to_log(['sox', path, out_path, 'remix', '1', 'rate', '16000'], logfile)

    logfile.close()

