from pathlib import Path
import pandas as pd

speaker_dict = {}
filepaths = [str(p) for p in Path('/Volumes/Files/Corpora/Corpora/Emotional corpus/Accepted/intended/ShEMO/').rglob('*.wav')]
filepaths = sorted(filepaths)

for path in filepaths:
    split_path = path.split('/')
    basis_name = split_path[-1][:-4]
    if basis_name.startswith('.'):
        print('Skipping hidden file: %s' % basis_name)
        continue

    speaker_number = int(basis_name[1:3])

    # Add padding for females
    if basis_name[0] == 'F':
        speaker_number += 100

    speaker_dict[speaker_number] = basis_name[0]

pd.DataFrame({
    'data_grouping': ['speaker']*len(speaker_dict),
    'new_label': ['sex']*len(speaker_dict),
    'key': list(speaker_dict.keys()),
    'value': list(speaker_dict.values())
}).to_csv('ShEMO.csv', index=False)
