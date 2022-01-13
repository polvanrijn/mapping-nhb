import argparse, os
from glob import glob
import xml.etree.ElementTree as ET
import pandas as pd
import subprocess
from src.libs.IO import IO

log_path = 'gemep.json'
log = IO.initialize_log(log_path)

parser = argparse.ArgumentParser(description='Restore gemep')
parser.add_argument('-i','--in_dir', required=True)
parser.add_argument('-o', '--out_dir', required=True)
args = parser.parse_args()

EMOTIONS = {
'admiration': 'ADM',
 'amusement': 'AMU',
 'anxiety': 'ANX',
 'cold_anger': 'CAN',
 'contempt': 'CON',
 'despair': 'DES',
 'disgust': 'DIS',
 'elation': 'ELA',
 'hot_anger': 'HAN',
 'interest': 'INt',
 'panic_fear': 'PAN',
 'pleasure': 'PLE',
 'pride': 'PRI',
 'relief': 'REL',
 'sadness': 'SAD',
 'shame': 'SHA',
 'tenderness': 'TEN'
}

ANNOTATION_FILE = 'emotions*'


if not os.path.exists(args.in_dir):
    raise FileNotFoundError('Directory does not exist!')

os.makedirs(args.out_dir, exist_ok=True)

sub_dirs = [p for p in glob(args.in_dir + '/*') if os.path.isdir(p)]
for dir in sub_dirs:
    info = dir.split('/')[-1]
    _, gender, speaker = info.split('-')

    annotation_files = sorted(glob(os.path.join(dir, ANNOTATION_FILE)))
    assert len(annotation_files) == 2

    audio_in = dir + '/chunks.audio.wav'
    if not os.path.exists(audio_in):
        raise FileNotFoundError('Audio in is missing')

    xml = annotation_files[0]
    emotions = [i.attrib['name'] for i in ET.parse(xml).getroot().findall('./*/item')]
    csv = annotation_files[1]
    segments = pd.read_csv(csv, sep=';', header=None)
    segments.columns = ['start', 'end', 'emotion', 'confidence']
    for r in range(segments.shape[0]):
        row = segments.iloc[r, :]
        emotion = emotions[int(row['emotion'])]
        emotion = EMOTIONS[emotion]
        key = '%s_%d_%s' % (speaker, r, emotion)
        start = row['start']
        end = row['end']
        if key not in log:
            print('Remaining for this speaker(%s): %d (completed in total: %d)' % (speaker, (segments.shape[0] - (r + 1)), len(log)))
            tmp_path = args.out_dir + '/tmp.wav'

            subprocess.call(['sox', audio_in, tmp_path, 'trim', str(start), str(end-start)])
            subprocess.call(['play', tmp_path])

            sentence_input = input('1: “ne kal ibam sud molen!” (NKI), 2: “kun se mina lod belam?” (KSM), 0: vocalization, 9: reversed = ')
            while sentence_input not in ['1', '2', '0', '9']:
                sentence_input = input('1: “ne kal ibam sud molen!”, 2: “kun se mina lod belam?”, 0: vocalization, 9: reversed')

            if sentence_input == '1':
                sentence = 'NKI'
            elif sentence_input == '2':
                sentence = 'KSM'
            elif sentence_input == '0':
                sentence = 'VOC'
            else:
                sentence = 'REV'

            log[key] = {}
            log[key]['sentence'] = sentence
            IO.write_json(log, log_path)
        else:
            sentence = log[key]['sentence']

        out_path = args.out_dir + '/%d_%s_%s_%s_%s.wav' % (r, emotion, gender, speaker, sentence)
        subprocess.call(['sox', audio_in, out_path, 'trim', str(start), str(end - start)])

os.remove(tmp_path)