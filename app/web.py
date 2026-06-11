from pathlib import Path
from math import ceil

import pandas as pd
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from sklearn.model_selection import train_test_split

from app.services.ml import (
    LABELS,
    FeatureExtractor,
    NaiveBayesClassifier,
    evaluate,
    word_frequencies,
)
from app.services.preprocessor import TextPreprocessor
from app.services.store import store


web = Blueprint("web", __name__)
preprocessor = TextPreprocessor()


def normalize_dataset(frame):
    columns = {str(column).strip().lower(): column for column in frame.columns}
    text_column = columns.get("text")
    label_column = columns.get("sentimen") or columns.get("label")
    if not text_column or not label_column:
        raise ValueError("Dataset wajib memiliki kolom text dan sentimen/label.")

    def optional(*names):
        for name in names:
            if name in columns:
                return frame[columns[name]].fillna("").astype(str)
        return pd.Series([""] * len(frame), index=frame.index, dtype=str)

    data = pd.DataFrame(
        {
            "source_row": range(1, len(frame) + 1),
            "external_id": optional("id"),
            "source_url": optional("url"),
            "text": frame[text_column],
            "published_at": optional("createdat", "created_at"),
            "author_profile_picture": optional(
                "author.profilepicture", "author_profile_picture"
            ),
            "label": frame[label_column],
            "label_reason": optional("alasan", "label_reason"),
            "label_status": optional("status_label", "label_status"),
        }
    )
    data["text"] = data["text"].fillna("").astype(str)
    data["label"] = data["label"].fillna("").astype(str).str.strip().str.lower()
    if data.empty:
        raise ValueError("File tidak mengandung data untuk diproses.")
    if len(data) > 50000:
        raise ValueError("Dataset melebihi batas 50.000 baris.")
    return data


def load_frame(source):
    try:
        return normalize_dataset(pd.read_excel(source))
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("File tidak dapat dibaca. Silakan unggah file .xlsx yang valid.") from exc


def ensure_dataset():
    if store.dataset is None:
        path = Path(current_app.config["DEFAULT_DATASET"])
        if path.exists():
            store.dataset = load_frame(path)
            store.dataset_filename = path.name
            save_dataset_to_database()
    return store.dataset is not None


def database():
    return current_app.extensions["database"]


def database_call(method, *args):
    db = database()
    if not db.available:
        return None
    try:
        return getattr(db, method)(*args)
    except Exception as exc:
        db.available = False
        db.error = str(exc)
        flash("Proses berjalan, tetapi penyimpanan database gagal.", "warning")
        return None


def save_dataset_to_database():
    if store.dataset is not None and store.dataset_id is None:
        store.dataset_id = database_call(
            "save_dataset",
            store.dataset,
            store.dataset_filename or "Dataset.xlsx",
        )


def require_step(step, endpoint):
    if store.step < step:
        flash("Selesaikan tahap sebelumnya terlebih dahulu.", "warning")
        return redirect(url_for(endpoint))
    return None


@web.app_context_processor
def inject_navigation():
    db = database()
    return {
        "pipeline_step": store.step,
        "labels_order": LABELS,
        "database_online": db.available,
        "database_name": db.database,
    }


@web.route("/")
def index():
    return redirect(url_for("web.import_data"))


@web.route("/import", methods=["GET", "POST"])
def import_data():
    if request.method == "POST":
        uploaded = request.files.get("dataset")
        try:
            if not uploaded or not uploaded.filename:
                raise ValueError("Pilih file dataset terlebih dahulu.")
            if not uploaded.filename.lower().endswith(".xlsx"):
                raise ValueError("Format file tidak didukung. Hanya .xlsx yang diterima.")
            frame = load_frame(uploaded)
            store.reset()
            store.dataset = frame
            store.dataset_filename = uploaded.filename
            save_dataset_to_database()
            flash(f"Dataset berhasil dimuat: {len(frame):,} baris.", "success")
        except ValueError as exc:
            flash(str(exc), "error")
    else:
        try:
            ensure_dataset()
        except ValueError as exc:
            flash(str(exc), "error")

    data = store.dataset
    counts = data["label"].value_counts().to_dict() if data is not None else {}
    invalid = data.loc[~data["label"].isin(LABELS)] if data is not None else None
    return render_template(
        "import.html",
        data=data,
        counts=counts,
        invalid_count=0 if invalid is None else len(invalid),
    )


@web.route("/preprocessing", methods=["GET", "POST"])
def preprocessing():
    if not ensure_dataset():
        return redirect(url_for("web.import_data"))
    if request.method == "POST" or store.preprocessed is None:
        data = store.dataset.copy()
        data["preprocessed"] = data["text"].map(preprocessor.preprocess)
        store.excluded_count = int(data["preprocessed"].eq("").sum())
        database_call(
            "save_preprocessing", store.dataset_id, data, store.excluded_count
        )
        store.preprocessed = data.loc[data["preprocessed"].ne("")].reset_index(drop=True)
        store.extractor = None
        store.matrix = None
        store.classifier = None
        store.evaluation = None
        flash("Preprocessing selesai dijalankan.", "success")
    return render_template(
        "preprocessing.html",
        data=store.preprocessed,
        excluded_count=store.excluded_count,
    )


@web.route("/labels")
def labels():
    blocked = require_step(2, "web.preprocessing")
    if blocked:
        return blocked
    data = store.preprocessed
    invalid = data.loc[~data["label"].isin(LABELS)]
    return render_template(
        "labels.html",
        counts=data["label"].value_counts().to_dict(),
        invalid=invalid,
        total=len(data),
    )


@web.route("/tfidf", methods=["GET", "POST"])
def tfidf():
    blocked = require_step(2, "web.preprocessing")
    if blocked:
        return blocked
    if request.method == "POST" or store.matrix is None:
        if not store.preprocessed["label"].isin(LABELS).all():
            flash("Perbaiki label tidak valid sebelum ekstraksi fitur.", "error")
            return redirect(url_for("web.labels"))
        store.extractor = FeatureExtractor()
        store.matrix = store.extractor.fit_transform(store.preprocessed["preprocessed"])
        store.top_terms = store.extractor.top_terms()
        store.classifier = None
        store.evaluation = None
        flash("Matriks TF-IDF berhasil dibuat.", "success")
    return render_template(
        "tfidf.html",
        shape=store.matrix.shape,
        top_terms=store.top_terms,
    )


@web.route("/classification", methods=["GET", "POST"])
def classification():
    blocked = require_step(4, "web.tfidf")
    if blocked:
        return blocked
    if request.method == "POST" or store.classifier is None:
        test_size = float(request.form.get("test_size", 0.2))
        class_counts = store.preprocessed["label"].value_counts()
        if int(class_counts.min()) < 2:
            flash(
                "Data tidak cukup: setiap kelas memerlukan minimal 2 sampel.",
                "error",
            )
            return redirect(url_for("web.labels"))
        test_count = max(ceil(len(store.preprocessed) * test_size), len(class_counts))
        if len(store.preprocessed) - test_count < len(class_counts):
            flash(
                "Data tidak cukup untuk membentuk data latih dan data uji stratified.",
                "error",
            )
            return redirect(url_for("web.labels"))
        x_train, x_test, y_train, y_test = train_test_split(
            store.matrix,
            store.preprocessed["label"],
            test_size=test_count,
            random_state=42,
            stratify=store.preprocessed["label"],
        )
        classifier = NaiveBayesClassifier()
        classifier.train(x_train, y_train)
        store.classifier = classifier
        store.x_train, store.x_test = x_train, x_test
        store.y_train, store.y_test = y_train, y_test
        store.predictions = classifier.predict(x_test)
        store.evaluation = evaluate(y_test, store.predictions)
        store.split = {
            "train": x_train.shape[0],
            "test": x_test.shape[0],
            "ratio": test_size,
        }
        store.training_id = database_call(
            "save_training",
            store.dataset_id,
            store.split,
            store.matrix.shape[1],
            store.top_terms,
            store.evaluation,
        )
        flash("Model Naive Bayes berhasil dilatih.", "success")
    return render_template("classification.html", split=store.split)


@web.route("/evaluation")
def evaluation():
    blocked = require_step(5, "web.classification")
    if blocked:
        return blocked
    return render_template("evaluation.html", result=store.evaluation)


@web.route("/dashboard")
def dashboard():
    blocked = require_step(5, "web.classification")
    if blocked:
        return blocked
    data = store.preprocessed
    counts = data["label"].value_counts().to_dict()
    frequencies = {
        label: word_frequencies(data.loc[data["label"].eq(label), "preprocessed"])
        for label in LABELS
    }
    return render_template(
        "dashboard.html",
        counts=counts,
        count_values=[int(counts.get(label, 0)) for label in LABELS],
        result=store.evaluation,
        frequencies=frequencies,
        total=len(data),
    )


@web.route("/prediction", methods=["GET", "POST"])
def prediction():
    blocked = require_step(5, "web.classification")
    if blocked:
        return blocked
    prediction_result = None
    text = ""
    if request.method == "POST":
        text = request.form.get("text", "").strip()
        processed = preprocessor.preprocess(text)
        if not text:
            flash("Silakan masukkan teks opini untuk dianalisis.", "error")
        elif not processed:
            flash("Teks tidak mengandung kata bermakna.", "error")
        else:
            matrix = store.extractor.transform([processed])
            label = store.classifier.predict(matrix)[0]
            probabilities = store.classifier.predict_proba(matrix)[0]
            prediction_result = {
                "label": label,
                "processed": processed,
                "probabilities": dict(
                    zip(store.classifier.model.classes_, probabilities.tolist())
                ),
            }
            database_call(
                "save_prediction",
                store.training_id,
                text,
                processed,
                label,
                prediction_result["probabilities"],
            )
    return render_template(
        "prediction.html", prediction=prediction_result, text=text
    )


@web.route("/database")
def database_status():
    db = database()
    stats = database_call("statistics") if db.available else {}
    return render_template(
        "database.html",
        online=db.available,
        error=db.error,
        database_name=db.database,
        stats=stats or {},
    )
