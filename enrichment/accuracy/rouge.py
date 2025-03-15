from rouge_score import rouge_scorer

from enrichment.accuracy.base_accuracy import BaseAccuracy


class Rouge(BaseAccuracy):

    def run(self, new_description: str, base_description: str):
        scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
        scores = scorer.score(base_description, new_description)

        return scores['rougeL'].fmeasure