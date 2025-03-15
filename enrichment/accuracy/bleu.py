from nltk.translate.bleu_score import sentence_bleu

from enrichment.accuracy.base_accuracy import BaseAccuracy

class Bleu(BaseAccuracy):
    def run(self, new_description: str, base_description: str):
        bleu_score = sentence_bleu([base_description.split()], new_description.split())
        return bleu_score