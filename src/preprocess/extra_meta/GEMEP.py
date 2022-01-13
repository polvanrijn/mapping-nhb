from pathlib import Path
import pandas as pd

filepaths = [str(p) for p in
             Path('/Volumes/Files/Corpora/Corpora/Emotional corpus/Accepted/intended/GEMEP/').rglob('*.wav')]
filepaths = sorted(filepaths)
speaker_dict = {}
for path in filepaths:
    basis_name = path.split('/')[-1][:-4]
    if basis_name.startswith('.'):
        print('Skipping hidden file: %s' % basis_name)
        continue

    _, emotion, gender, speaker, sentence = basis_name.split('_')
    speaker_dict[int(speaker)] = gender.upper()

pd.DataFrame({
    'data_grouping': ['speaker']*len(speaker_dict),
    'new_label': ['sex']*len(speaker_dict),
    'key': list(speaker_dict.keys()),
    'value': list(speaker_dict.values())
}).to_csv('GEMEP.csv', index=False)
