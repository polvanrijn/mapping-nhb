from glob import glob
import pandas as pd
speaker_dict = {}
filepaths = glob('/Volumes/Files/Corpora/Corpora/Emotional corpus/Accepted/intended/MSP_improv/audio/session*/session*/*/[R, T]/*.wav')
filepaths = sorted(filepaths)

for path in filepaths:
    split_path = path.split('/')
    basis_name = split_path[-1][:-4]
    if basis_name.startswith('.'):
        print('Skipping hidden file: %s' % basis_name)
        continue

    _, _, sentence_emotion, speaker, task, listener_speaker_turn = basis_name.split('-')

    # Speaker format [M|F][session]
    speaker_number = (int(speaker[-2:]) - 1) * 2
    if speaker[0] == 'M':
        speaker_number += 1
    elif speaker[0] == 'F':
        speaker_number += 2
    else:
        raise NotImplementedError('Male is coded as uneven numbers, female as even numbers')
    speaker_dict[speaker_number] = speaker[0]


pd.DataFrame({
    'data_grouping': ['speaker']*len(speaker_dict),
    'new_label': ['sex']*len(speaker_dict),
    'key': list(speaker_dict.keys()),
    'value': list(speaker_dict.values())
}).to_csv('MSP_improv.csv', index=False)
