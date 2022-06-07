# -*- coding: utf-8 -*-
"""
Created on Sun May 15 09:30:06 2022
@author: Nicola
"""

from happytransformer import HappyTextClassification

class Sentiment():
    def __init__(self):
        self.htc_sentiment = HappyTextClassification(model_type="BERT", model_name="neuraly/bert-base-italian-cased-sentiment", num_labels=3)

    def ottieni_sentiment(self, testo):
        risultato = self.htc_sentiment.classify_text(testo)
        if risultato.label == "positive":
            return "positivo", risultato.score
        elif risultato.label == "negative":
            return "negativo", risultato.score
        else:
            return "neutrale", risultato.score


class Feel():
    def __init__(self):
        self.htc_feel = HappyTextClassification(model_type="BERT", model_name="MilaNLProc/feel-it-italian-emotion", num_labels=4)
        
    def ottieni_feel(self, testo):
        risultato = self.htc_feel.classify_text(testo)
        if risultato.label == "anger":
            return "rabbia"
        elif risultato.label == "joy":
            return "gioia"
        elif risultato.label == "fear":
            return "paura"
        else:
            return "tristezza"