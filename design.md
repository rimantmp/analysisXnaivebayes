# Design Document: Sentiment Analysis Pinjol

## Overview

Aplikasi web admin dashboard untuk analisis sentimen opini masyarakat terhadap pinjaman online (pinjol) di media sosial X menggunakan algoritma Naïve Bayes. Dibangun sebagai **Flask monolith** — satu aplikasi Python yang menangani routing, server-side rendering (Jinja2), dan seluruh komputasi NLP/ML tanpa dependency JavaScript build tools.

### Key Design Decisions

1. **Flask + Jinja2 (server-side rendering)** — Tidak perlu React/Node.js. Semua halaman di-render di server menggunakan Jinja2 templates. Sederhana, satu stack, mudah di-deploy.
2. **Tailwind CSS via CDN** — Styling admin dashboard tanpa npm build step.
3. **Chart.js via CDN** — Visualisasi interaktif (pie chart, bar chart) di browser. Data dikirim dari Flask sebagai JSON di template.
4. **Scikit-learn** — MultinomialNB dan TfidfVectorizer yang teruji dan production-ready.
5. **PySastrawi** — Library stemming bahasa Indonesia standar.
6. **WordCloud library** — Generate word cloud sebagai PNG di server.
7. **In-memory state** — Dataset dan model disimpan dalam memory selama session. Cocok untuk tool analisis single-user.
8. **Dataset pre-labeled** — File Dataset.xlsx sudah memiliki label sentimen (positif, negatif, netral).

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Flask Application                    │
├─────────────────────────────────────────────────────┤
│  Routes (Blueprint)                                   │
│  ├── /import        → Import & validasi dataset       │
│  ├── /preprocessing → Pipeline preprocessing          │
│  ├── /labels        → Validasi & distribusi label     │
│  ├── /tfidf         → Ekstraksi fitur TF-IDF         │
│  ├── /classification→ Split, train, predict           │
│  ├── /evaluation    → Metrik evaluasi model           │
│  ├── /dashboard     → Visualisasi hasil               │
│  └── /prediction    → Prediksi teks baru              │
├─────────────────────────────────────────────────────┤
│  Services Layer                                       │
│  ├── TextPreprocessor (cleaning, stemming, stopwords) │
│  ├── FeatureExtractor (TF-IDF vectorization)         │
│  ├── NaiveBayesClassifier (train, predict, proba)    │
│  ├── ModelEvaluator (accuracy, precision, recall, F1)│
│  └── SessionStore (in-memory state management)       │
├─────────────────────────────────────────────────────┤
│  Templates (Jinja2 + Tailwind CSS)                   │
│  ├── base.html (sidebar layout)                      │
│  └── pages/ (satu template per fitur)                │
├─────────────────────────────────────────────────────┤
│  Static Assets                                        │
│  ├── generated/ (word cloud PNGs)                    │
│  └── css/ (custom styles jika perlu)                 │
└─────────────────────────────────────────────────────┘
```

### Data Flow Pipeline

```
Upload .xlsx → Import & Validate → Preprocessing → TF-IDF → Split Data → Train NB → Evaluate → Dashboard
                                                                                    ↓
                                                                              Predict New Text
```

### Request Flow (Server-Side Rendering)

```
Browser Request → Flask Route → Service Layer (computation) → Jinja2 Template → HTML Response
```

Setiap halaman:
1. Browser mengirim GET/POST request
2. Flask route memanggil service layer untuk komputasi
3. Hasil dikirim ke Jinja2 template sebagai context variables
4. Template di-render menjadi HTML lengkap dan dikirim ke browser
5. Chart.js menerima data via `<script>` tag berisi JSON dari Jinja2

## Components and Interfaces

### Project Structure

```
sentiment-analysis-pinjol/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # App configuration
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── import_data.py       # /import routes
│   │   ├── preprocessing.py     # /preprocessing routes
│   │   ├── labels.py            # /labels routes
│   │   ├── tfidf.py             # /tfidf routes
│   │   ├── classification.py    # /classification routes
│   │   ├── evaluation.py        # /evaluation routes
│   │   ├── dashboard.py         # /dashboard routes
│   │   └── prediction.py        # /prediction routes
│   ├── services/
│   │   ├── __init__.py
│   │   ├── preprocessor.py      # Text preprocessing pipeline
│   │   ├── feature_extractor.py # TF-IDF vectorization
│   │   ├── classifier.py        # Naïve Bayes wrapper
│   │   ├── evaluator.py         # Model evaluation metrics
│   │   └── store.py             # In-memory session store
│   ├── templates/
│   │   ├── base.html            # Base layout with sidebar
│   │   ├── import.html          # Import dataset page
│   │   ├── preprocessing.html   # Preprocessing results
│   │   ├── labels.html          # Label validation page
│   │   ├── tfidf.html           # TF-IDF results page
│   │   ├── classification.html  # Classification page
│   │   ├── evaluation.html      # Evaluation metrics page
│   │   ├── dashboard.html       # Visualization dashboard
│   │   └── prediction.html      # Single text prediction
│   └── static/
│       └── generated/           # Word cloud images
├── tests/
│   ├── unit/
│   ├── property/
│   └── integration/
├── Dataset.xlsx                 # Pre-labeled dataset
├── requirements.txt             # Python dependencies
└── run.py                       # Entry point
```

### Backend Services

#### 1. TextPreprocessor (`app/services/preprocessor.py`)

```python
class TextPreprocessor:
    def __init__(self):
        self.stemmer = StemmerFactory().create_stemmer()
        self.stopwords: Set[str]  # Indonesian stopword list
    
    def clean(self, text: str) -> str:
        """Remove URLs, mentions, hashtags, numbers, non-alpha chars"""
    
    def case_fold(self, text: str) -> str:
        """Convert to lowercase"""
    
    def tokenize(self, text: str) -> List[str]:
        """Split by whitespace"""
    
    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        """Remove Indonesian stopwords"""
    
    def stem(self, tokens: List[str]) -> List[str]:
        """Apply Sastrawi stemming"""
    
    def preprocess(self, text: str) -> str:
        """Full pipeline: clean → fold → tokenize → stopwords → stem → join"""
```

#### 2. FeatureExtractor (`app/services/feature_extractor.py`)

```python
class FeatureExtractor:
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
    
    def fit_transform(self, documents: List[str]) -> sparse_matrix:
        """Build TF-IDF matrix from documents"""
    
    def transform(self, documents: List[str]) -> sparse_matrix:
        """Transform new documents using fitted vectorizer"""
    
    def get_top_terms(self, n: int = 20) -> List[Tuple[str, float]]:
        """Top N terms by average TF-IDF score"""
    
    def get_matrix_shape(self) -> Tuple[int, int]:
        """(n_documents, n_terms)"""
```

#### 3. NaiveBayesClassifier (`app/services/classifier.py`)

```python
class NaiveBayesClassifier:
    def __init__(self, alpha: float = 1.0):
        self.model = MultinomialNB(alpha=alpha)
        self.is_trained: bool = False
    
    def train(self, X_train, y_train) -> None:
        """Train model"""
    
    def predict(self, X) -> ndarray:
        """Predict labels"""
    
    def predict_proba(self, X) -> ndarray:
        """Predict probabilities per class"""
    
    def get_classes(self) -> List[str]:
        """Return class labels"""
```

#### 4. ModelEvaluator (`app/services/evaluator.py`)

```python
class ModelEvaluator:
    def evaluate(self, y_true, y_pred, labels) -> dict:
        """Return accuracy, precision, recall, F1, confusion matrix"""
    
    def get_confusion_matrix(self, y_true, y_pred, labels) -> ndarray:
        """3x3 confusion matrix"""
    
    def get_classification_report(self, y_true, y_pred, labels) -> dict:
        """Per-class metrics + macro average"""
```

#### 5. SessionStore (`app/services/store.py`)

```python
class SessionStore:
    """Singleton in-memory store for application state"""
    
    dataset: Optional[pd.DataFrame] = None
    preprocessed_data: Optional[pd.DataFrame] = None
    tfidf_matrix: Optional[sparse_matrix] = None
    vectorizer: Optional[FeatureExtractor] = None
    X_train = None
    X_test = None
    y_train = None
    y_test = None
    classifier: Optional[NaiveBayesClassifier] = None
    predictions: Optional[ndarray] = None
    evaluation: Optional[dict] = None
    
    def reset(self):
        """Clear all state"""
    
    def get_pipeline_step(self) -> str:
        """Return current pipeline progress"""
```

### Flask Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Redirect to `/import` |
| `/import` | GET/POST | Upload .xlsx, show preview |
| `/preprocessing` | GET/POST | Run preprocessing, show results |
| `/labels` | GET | Validate labels, show distribution |
| `/tfidf` | GET/POST | Compute TF-IDF, show top terms |
| `/classification` | GET/POST | Split + train + predict |
| `/evaluation` | GET | Show metrics + confusion matrix |
| `/dashboard` | GET | Visualization dashboard |
| `/prediction` | GET/POST | Single text prediction |

### Jinja2 Template Structure

**base.html** — Admin dashboard layout:
```html
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body class="bg-gray-50">
    <!-- Sidebar Navigation -->
    <aside class="fixed w-64 h-full bg-white border-r">
        <!-- Logo + Nav menu items -->
    </aside>
    
    <!-- Main Content -->
    <main class="ml-64 p-8">
        {% block content %}{% endblock %}
    </main>
</body>
</html>
```

### Sentiment Color System (Tailwind Classes)

| Sentimen | Background | Text | Badge |
|----------|-----------|------|-------|
| Positif | `bg-green-50` | `text-green-700` | `bg-green-100 border-green-300` |
| Negatif | `bg-red-50` | `text-red-700` | `bg-red-100 border-red-300` |
| Netral | `bg-slate-50` | `text-slate-700` | `bg-slate-100 border-slate-300` |

## Data Models

### DataFrame Schema (after import)

| Column | Type | Description |
|--------|------|-------------|
| `text` | str | Original tweet text |
| `label` | str | Sentiment label (positif/negatif/netral) |
| `preprocessed` | str | Text after preprocessing pipeline |

### Naïve Bayes Algorithm Detail

Multinomial Naïve Bayes dengan Laplace smoothing:

```
P(class | document) ∝ P(class) × ∏ P(term_i | class)

Prior:      P(class) = count(class) / total_documents
Likelihood: P(term | class) = (count(term, class) + α) / (total_terms_in_class + α × vocab_size)
Prediction: argmax_class P(class | document)

α = 1 (Laplace smoothing)
```

### Dependencies (requirements.txt)

```
flask>=3.0
pandas>=2.0
openpyxl>=3.1
scikit-learn>=1.3
PySastrawi>=1.4
nltk>=3.8
wordcloud>=1.9
matplotlib>=3.7
numpy>=1.24
```

## Correctness Properties

### Property 1: Distribution Computation Consistency

*For any* valid dataset, sum of counts per label equals total rows.

**Validates: Requirements 1.2, 3.2**

### Property 2: Text Cleaning Removes Unwanted Patterns

*For any* text containing URLs, mentions, hashtags, numbers, or non-alpha chars, after cleaning only alphabetic characters and spaces remain.

**Validates: Requirements 2.1**

### Property 3: Case Folding Produces Lowercase

*For any* text, after case folding, no uppercase characters exist and length is preserved.

**Validates: Requirements 2.2**

### Property 4: Tokenization Produces Valid Tokens

*For any* non-empty cleaned text, tokenization produces tokens that are all non-empty and contain no whitespace.

**Validates: Requirements 2.3**

### Property 5: Stopword Removal Completeness

*For any* token list, after stopword removal, no remaining token exists in the stopword dictionary.

**Validates: Requirements 2.4**

### Property 6: Empty Text Exclusion

*For any* text that becomes empty after preprocessing, it is excluded from classification and counted in the exclusion list.

**Validates: Requirements 2.7**

### Property 7: Label Validation Correctness

*For any* dataset, the validator identifies exactly those rows with labels not in {"positif", "negatif", "netral"} (case-insensitive).

**Validates: Requirements 3.4**

### Property 8: TF-IDF Matrix Invariants

*For any* set of non-empty documents, TF-IDF matrix has shape (n_docs, n_terms), all values ≥ 0, every row has at least one non-zero value.

**Validates: Requirements 4.1**

### Property 9: Top Terms Ordering

*For any* N, top-N terms are in non-increasing order of average TF-IDF score.

**Validates: Requirements 4.3**

### Property 10: Split Ratio Correctness

*For any* dataset and ratio, train_count + test_count = total, and same seed produces identical splits.

**Validates: Requirements 5.2**

### Property 11: Stratified Split Proportionality

*For any* dataset with ≥2 samples per class, label proportions in train/test are within ±5% of original.

**Validates: Requirements 5.4**

### Property 12: Prediction Validity

*For any* non-empty input, prediction produces exactly one label from {positif, negatif, netral} and probabilities sum to 1.0 (±0.001).

**Validates: Requirements 6.2, 9.3**

### Property 13: Prior Probabilities Sum to Unity

*For any* training set, P(positif) + P(negatif) + P(netral) = 1.0.

**Validates: Requirements 6.3**

### Property 14: Evaluation Metrics Consistency

*For any* predictions: accuracy ∈ [0,1], confusion matrix row sums = actual class counts, F1 = 2PR/(P+R).

**Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5**

### Property 15: Word Frequency Ordering

*For any* corpus, top-N words are in non-increasing frequency order.

**Validates: Requirements 8.3**

### Property 16: Preprocessing Idempotency per Document

*For any* text, preprocessing result is independent of other documents in the batch.

**Validates: Requirements 9.2**

## Error Handling

| Error | Trigger | Message | Recovery |
|-------|---------|---------|----------|
| Format invalid | Non-.xlsx upload | "Format file tidak didukung. Hanya .xlsx yang diterima." | Re-upload |
| Missing columns | No text/label column | "Kolom [nama] tidak ditemukan dalam file." | Re-upload |
| Empty file | No data rows | "File tidak mengandung data untuk diproses." | Re-upload |
| Corrupt file | Unreadable .xlsx | "File tidak dapat dibaca. Silakan unggah file yang valid." | Re-upload |
| Size exceeded | > 50,000 rows | "Dataset melebihi batas 50.000 baris." | Re-upload |
| Invalid labels | Label ∉ {positif,negatif,netral} | List invalid rows, block classification | Fix dataset |
| Insufficient data | < 2 per class | "Data tidak cukup untuk stratified split." | Larger dataset |
| No valid docs | All empty after preprocessing | "Tidak ada data valid untuk ekstraksi fitur." | Check dataset |
| Model not trained | Predict before train | "Model harus dilatih terlebih dahulu." | Complete training |
| Empty input | Blank prediction text | "Silakan masukkan teks tweet untuk dianalisis." | Enter text |
| Empty after preprocess | Input empty after cleaning | "Teks tidak mengandung kata bermakna." | Try different text |

### Error Display Strategy

- Errors shown as dismissible alert banners (Tailwind `bg-red-50 border-red-300`)
- Page state preserved on error — no full page reload needed
- Flash messages via Flask `flash()` for post-redirect-get pattern
- Loading state shown via simple spinner overlay during form submission

## Testing Strategy

### Property-Based Testing (Hypothesis)

```
tests/property/
├── test_preprocessing_props.py   # Properties 2-6, 16
├── test_data_props.py            # Properties 1, 7, 10-11
├── test_tfidf_props.py           # Properties 8-9, 15
├── test_classifier_props.py      # Properties 12-13
└── test_evaluator_props.py       # Property 14
```

**Configuration:** Minimum 100 iterations per property, custom strategies for Indonesian text generation.

### Unit Testing (pytest)

```
tests/unit/
├── test_preprocessor.py          # Specific Indonesian text examples
├── test_feature_extractor.py     # TF-IDF edge cases
├── test_classifier.py            # NB wrapper behavior
├── test_evaluator.py             # Metrics computation
└── test_validators.py            # Input validation
```

### Integration Testing

```
tests/integration/
├── test_routes.py                # Flask route responses
├── test_file_upload.py           # .xlsx upload handling
└── test_full_pipeline.py         # End-to-end workflow
```

### Test Runner

```bash
pytest tests/ -v --tb=short
```
