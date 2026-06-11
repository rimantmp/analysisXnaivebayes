import re

from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory


class TextPreprocessor:
    def __init__(self):
        self.stemmer = StemmerFactory().create_stemmer()
        self.stopwords = set(StopWordRemoverFactory().get_stop_words())
        self.stopwords.update(
            {"yg", "ga", "gak", "nggak", "nya", "nih", "sih", "aja", "rt", "amp"}
        )

    def clean(self, text):
        text = str(text or "")
        text = re.sub(r"https?://\S+|www\.\S+", " ", text)
        text = re.sub(r"@\w+", " ", text)
        text = re.sub(r"#(\w+)", r" \1 ", text)
        text = re.sub(r"\d+", " ", text)
        text = re.sub(r"[^A-Za-zÀ-ÖØ-öø-ÿ\s]", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def case_fold(self, text):
        return text.lower()

    def tokenize(self, text):
        return text.split()

    def remove_stopwords(self, tokens):
        return [token for token in tokens if token not in self.stopwords and len(token) > 1]

    def stem(self, tokens):
        return [self.stemmer.stem(token) for token in tokens]

    def preprocess(self, text):
        cleaned = self.case_fold(self.clean(text))
        tokens = self.remove_stopwords(self.tokenize(cleaned))
        return " ".join(token for token in self.stem(tokens) if token)
