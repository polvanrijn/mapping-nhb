# You must make sure you have ffmpeg, sox and OpenSMILE installed on the server
import argparse, os
from multiprocessing import cpu_count
from tqdm import tqdm
import shutil
from glob import glob

supported_corpora = []
for d in glob('datasets/[!_]*.py'):
    supported_corpora.append(d.split('/')[-1][:-3])

parser = argparse.ArgumentParser(description='Preprocess')
parser.add_argument('--dataset', choices=supported_corpora, required=True)
parser.add_argument('--in_dir')
parser.add_argument('--out_dir')
parser.add_argument('--num_workers', type=int, default=cpu_count())
args = parser.parse_args()


in_dir = args.in_dir + args.dataset + '/'
if not os.path.exists(in_dir):
    exit('Path %s does not exist' % in_dir)

# Sorry this is very hacky...
# It just imports the function `build_from_path` from each of the specialisations
build_from_path = getattr(__import__('datasets.%s' % args.dataset, fromlist=['build_from_path']), 'build_from_path')

if args.dataset not in supported_corpora:
    exit('Unknown corpus')

out_dir = args.out_dir + args.dataset + '/preprocessed/'
if os.path.exists(out_dir):
    shutil.rmtree(out_dir)
os.makedirs(out_dir, exist_ok=True)
build_from_path(in_dir, out_dir, args.num_workers, tqdm)
