from pathlib import Path
import pandas as pd
import os

speaker_dict = {}
speaker_mapping = {}
filepaths = sorted(
    [str(p) for p in Path('/Volumes/Files/Corpora/Corpora/Emotional corpus/Accepted/intended/VENEC/').rglob('*.wav')])
filepaths.extend(sorted(
    [str(p) for p in Path('/Volumes/Files/Corpora/Corpora/Emotional corpus/Accepted/intended/VENEC/').rglob('*.WAV')]))

for idx, path in enumerate(filepaths):
    basis_name = os.path.basename(path)[:-4]
    if basis_name.startswith('.'):
        continue
    country, speaker_emo = basis_name.split('_')
    speaker = speaker_emo[:-3]

    speaker_number = int(speaker)

    if country == 'IN':
        speaker_number += 25
    elif country == 'KE':
        speaker_number += 50
    elif country == 'SI':
        speaker_number += 75
    elif country == 'US':
        speaker_number += 100

    speaker_dict[speaker_number] = country
    speaker_mapping[speaker_number] = speaker

pd.DataFrame({
    'data_grouping': ['speaker'] * len(speaker_dict),
    'new_label': ['country'] * len(speaker_dict),
    'key': list(speaker_dict.keys()),
    'value': list(speaker_dict.values())
}).append(
    pd.DataFrame({
        'data_grouping': ['speaker'] * len(speaker_mapping),
        'new_label': ['sex'] * len(speaker_mapping),
        'key': list(speaker_mapping.keys()),
        'value': list(speaker_mapping.values())
    }), ignore_index=True
).sort_values(
    by=['key', 'new_label']
).to_csv('VENEC_tmp.csv', index=False)
