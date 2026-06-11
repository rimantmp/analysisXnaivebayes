from collections import Counter

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.naive_bayes import MultinomialNB


LABELS = ["positif", "netral", "negatif"]


class FeatureExtractor:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=10000)
        self.matrix = None

    def fit_transform(self, documents):
        self.matrix = self.vectorizer.fit_transform(documents)
        return self.matrix

    def transform(self, documents):
        return self.vectorizer.transform(documents)

    def top_terms(self, n=20):
        means = np.asarray(self.matrix.mean(axis=0)).ravel()
        terms = self.vectorizer.get_feature_names_out()
        indexes = means.argsort()[::-1][:n]
        return [(terms[i], round(float(means[i]), 5)) for i in indexes]


class NaiveBayesClassifier:
    def __init__(self, alpha=1.0):
        self.model = MultinomialNB(alpha=alpha)

    def train(self, x_train, y_train):
        self.model.fit(x_train, y_train)

    def predict(self, matrix):
        return self.model.predict(matrix)

    def predict_proba(self, matrix):
        return self.model.predict_proba(matrix)


def evaluate(y_true, y_pred):
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=LABELS, average="macro", zero_division=0
    )
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "matrix": confusion_matrix(y_true, y_pred, labels=LABELS).tolist(),
        "report": classification_report(
            y_true, y_pred, labels=LABELS, output_dict=True, zero_division=0
        ),
    }


def word_frequencies(documents, n=15):
    return Counter(" ".join(documents).split()).most_common(n)
