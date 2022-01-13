from os import walk
from os.path import join, exists
import numpy as np
from subprocess import PIPE, run
from tqdm import tqdm
from glob import glob

import argparse
parser = argparse.ArgumentParser(description='Preprocess')
parser.add_argument('-p','--path', required=True)
parser.add_argument('--ext', required=False, default="wav")
args = parser.parse_args()

audio_path = args.path
extension = '.' + args.ext
if not exists(audio_path):
    raise ValueError('Audio directory does not exist.')

onlyfiles = [y for x in walk(audio_path) for y in glob(join(x[0], ('*' + extension)))]


all_durations = []
for file in tqdm(onlyfiles):
    if file.endswith(extension):
        result = run(['soxi', '-D', file], cwd=audio_path, stdout=PIPE, stderr=PIPE, universal_newlines=True)
        try:
            all_durations.append(float(result.stdout))
        except:
            print('Error occurred: %s' % result.stdout)

all_durations = np.array(all_durations)/60

print('Processed files: %d' % (len(onlyfiles)))
print('Total duration in minutes: %d' % sum(all_durations))
print('Avg duration in minutes: %d (SD: %.2f)' % (all_durations.mean(), all_durations.std()))