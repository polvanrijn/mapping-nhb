import argparse, os, subprocess
from glob import glob
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from multiprocessing import cpu_count
import time

parser = argparse.ArgumentParser(description='Extract openSMILE features')
parser.add_argument('-i','--input_folder', required=True)
parser.add_argument('-o','--output_file', required=True)
parser.add_argument('--feature_set', required=False, default=os.path.expanduser('~') + "/repos/opensmile-2.3.0/config/gemaps/eGeMAPSv01a.conf")
parser.add_argument('--num_workers', required=False, default=cpu_count())
args = parser.parse_args()

folder = args.input_folder
if not os.path.exists(folder):
    raise Exception('Folder does not exist!')

csv_path = args.output_file
if not csv_path.endswith('.csv'):
    raise NotImplementedError('Can only write to CSV for now')

if os.path.exists(csv_path):
    os.remove(csv_path)

config_path = args.feature_set
if not os.path.exists(config_path):
    raise Exception('Config file does not exist!')


def _process_utterance(config_path, filename, csv_path):
    core_name = os.path.basename(filename)
    if core_name == '' or core_name is None:
        print(filename)
    FNULL = open(os.devnull, 'w')
    a = subprocess.call(['SMILExtract', '-instname', core_name, '-C', config_path, "-I", filename, "-csvoutput", csv_path, "-appendcsv", '1'], stdout=FNULL, stderr=subprocess.STDOUT)

executor = ProcessPoolExecutor(max_workers=args.num_workers)
futures = []
csv_paths = []
print('Extracting features')
for filename in glob(os.path.join(folder, '*.wav')):
    basis_name = os.path.basename(filename)
    if basis_name.startswith('.'):
        print('Skip empty file: %s' % basis_name)
        continue
    filename_split = filename.split('.')
    csv_tmp_path = '.'.join(filename_split)[:-1] + '_tmp.csv'
    csv_paths.append(csv_tmp_path)
    task = partial(_process_utterance, config_path, filename, csv_tmp_path)
    futures.append(executor.submit(task))

results = [future.result() for future in tqdm(futures)]

# Wait for all results to be there
time.sleep(1)

def read_lines(txt_path):
    f = open(txt_path, 'r')
    lines = f.readlines()
    f.close()
    return lines

# write the header
with open(csv_path, 'w') as f:
    f.write(read_lines(csv_paths[-1])[0])

print('Concatinating dataframes')
for path in tqdm(csv_paths):
    if os.path.exists(path):
        with open(csv_path, 'a') as f:
            lines = read_lines(path)
            if len(lines) == 1:
                idx = 0
            else:
                idx = 1
            f.write(lines[idx])
        os.remove(path)
    else:
        print('Path not found: %s' % path)

