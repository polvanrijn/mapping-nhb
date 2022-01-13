# Extraction of features #

This part of the project is done on the computing cluster (HPC).

#### How do I get set up?

##### Requirements

- Compile `OpenSMILE`
- Install `ffmpeg` and `sox`



Preprocess each corpus, e.g.:

```bash
module load conda
# Make sure sox and ffmpeg are in the path
source activate production_MAPS
python preprocess.py --dataset NAME_OF_DATASET
```



Now extract the features, we used eGeMAPS:

```bash
module load conda
source activate production_MAPS
# Make sure OpenSMILE is in path, e.g.
# export PATH=${PATH}:$HOME/bin/opensmile
python extract_openSMLIE.py -i /path/to/corpus/NAME_OF_DATASET/preprocessed -o /path/to/corpus/NAME_OF_DATASET/eGeMAPS.csv
```
