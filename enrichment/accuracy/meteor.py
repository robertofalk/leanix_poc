import nltk
from nltk.translate.meteor_score import single_meteor_score

from enrichment.accuracy.base_accuracy import BaseAccuracy

class Meteor(BaseAccuracy):

    def __init__(self) -> None:
        nltk.download('wordnet')

    def run(self, new_description: str, base_description: str):
        meteor_score = single_meteor_score(base_description.split(), new_description.split())
        return meteor_score