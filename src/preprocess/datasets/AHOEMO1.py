from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path
from src.preprocess.helpers import num_to_letter, num_to_two_letters, num_to_three_letters, write_to_log
import subprocess
import os

FILENAME = 'ahoemo1.tar.gz'
EMOTIONS = {
    'anger': 'ANG',
    'disgust': 'DIS',
    'fear': 'FER',
    'happineess': 'HAP',  # KEEP THIS TYPO
    'neutral': 'NEU',
    'sadness': 'SAD',
    'surprise': 'SUR'
}
CORPUS_ABRV = 'AH1'
SPEAKER = num_to_two_letters(1)
REPETITION = num_to_letter(1)
INTENSITY = 'XX'
FOLDER_NAME = 'ahoemo1'
def build_from_path(in_dir, out_dir, num_workers=1, tqdm=lambda x: x):
    executor = ProcessPoolExecutor(max_workers=num_workers)
    futures = []
    folder = in_dir + FOLDER_NAME + '/'

    if not os.path.exists(folder):
        subprocess.call(['tar', '-zxvf', FILENAME], cwd=in_dir)
    else:
        print('Folder already exists. No need to extract the tar archive again.')

    for emotion, emo_abrv in EMOTIONS.items():
        print(emotion)
        filepaths = [str(p) for p in Path(folder + '%s/comunes/wav/wav_01/' % emotion).rglob('*.wav')]
        filepaths.extend(
            [str(p) for p in Path(folder + '%s/depend/wav/wav_01/' % emotion).rglob('*.wav')]
        )
        filepaths = sorted(filepaths)

        for idx, path in enumerate(filepaths):
            sentence = num_to_three_letters(idx + 1)
            task = partial(_process_utterance, path, out_dir, emo_abrv, sentence)
            futures.append(executor.submit(task))

        results = [future.result() for future in tqdm(futures)]
    return [r for r in results if r is not None]



def _process_utterance(path, out_dir, emo_abrv, sentence):
    logfile = open(out_dir + '%s_%s_%s_%s_%s_%s.log' % (CORPUS_ABRV, emo_abrv, sentence, SPEAKER, REPETITION, INTENSITY), 'w')

    # Downsample and only take the first channel
    out_path = out_dir + '%s_%s_%s_%s_%s_%s.wav' % (CORPUS_ABRV, emo_abrv, sentence, SPEAKER, REPETITION, INTENSITY)
    logfile = write_to_log(['sox', path, out_path, 'remix', '1', 'rate', '16000'], logfile)

    # Old code for comparison
    # sil_dir = os.path.join(out_dir, 'silence')
    # os.makedirs(sil_dir, exist_ok=True)
    # sil_path = os.path.join(sil_dir, '%s_%s_%s_%s_%s_%s.wav' % (CORPUS_ABRV, emo_abrv, sentence, SPEAKER, REPETITION, INTENSITY))
    # # Slice off silences at start and end of the fragment
    # remove_silence_cmd = [
    #         'ffmpeg', '-y',  # overwrite previous
    #         '-i', out_path,
    #         # remove silences
    #         '-af',
    #         'silenceremove=start_periods=1:start_duration=1:start_threshold=-70dB:detection=peak,aformat=dblp,areverse,silenceremove=start_periods=1:start_duration=1:start_threshold=-70dB:detection=peak,aformat=dblp,areverse',
    #         sil_path
    #     ]
    # logfile = write_to_log(remove_silence_cmd, logfile)

    logfile.close()
