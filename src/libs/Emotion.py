import pandas as pd
import os
from src.libs.IO import IO

class Emotion:
    def __init__(self):
        emotion_df = pd.read_csv(os.path.dirname(__file__) + '/emotions.csv', header=None)
        emotion_df.columns = ['code', 'emotion']
        self.emotions = [l.lower() for l in list(emotion_df['emotion'].values)]
        self.codes = list(emotion_df['code'].values)
        self.code_to_emo_dict = IO.zip_together(self.codes, self.emotions)
        self.emo_to_code_dict = IO.zip_together(self.emotions, self.codes)

    def code_to_emo(self, code):
        return IO.lookup(code, self.code_to_emo_dict, "This emotion code (%s) is not in our database")

    def emo_to_code(self, emotion):
        emotion = emotion.lower()
        if emotion == 'angry':
            emotion = 'anger'
        elif emotion == 'anxious':
            emotion = 'anxiety'
        elif emotion == 'bored':
            emotion = 'boredom'
        elif emotion == 'calm':
            emotion = 'calmness'
        elif emotion == 'depressed':
            emotion = 'depression'
        elif emotion == 'disgusted':
            emotion = 'disgust'
        elif emotion == 'disgusted':
            emotion = 'disgust'
        elif emotion == 'excited':
            emotion = 'excitement'
        elif emotion == 'fearful':
            emotion = 'fear'
        elif emotion == 'frustrated':
            emotion = 'frustration'
        elif emotion == 'happy':
            emotion = 'happiness'
        elif emotion == 'helpless':
            emotion = 'helplessness'
        elif emotion == 'ironic':
            emotion = 'irony'
        elif emotion == 'irritated':
            emotion = 'irritation'
        elif emotion == 'joyful':
            emotion = 'joy'
        elif emotion == 'neutrality':
            emotion = 'neutral'
        elif emotion == 'pleasant surprise':
            emotion = 'positive surprise'
        elif emotion == 'stressed':
            emotion = 'stress'

        # Rename synonym emotions
        if emotion == 'sad':
            emotion = 'sadness'
        elif emotion == 'sarcastic':
            emotion = 'sarcasm'
        elif emotion == 'shyness':
            emotion = 'shy'
        elif emotion == 'surprised':
            emotion = 'surprise'
        elif emotion == 'mirth':
            emotion = 'happiness'
        elif emotion == 'tense' or emotion == 'pressure':
            emotion = 'stress'

        # Recoded
        elif emotion == "startle":
            emotion = 'surprise'
        elif emotion == 'gratification':
            emotion = 'pleasure'
        elif emotion == 'satisfaction':
            emotion = 'happiness'

        return IO.lookup(emotion, self.emo_to_code_dict, "This emotion (%s) is not in our database")