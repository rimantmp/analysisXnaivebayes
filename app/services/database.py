import hashlib
import json
import re
from contextlib import contextmanager

import pymysql
from pymysql.cursors import DictCursor


SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(120) NOT NULL,
        username VARCHAR(80) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        role ENUM('admin','operator') NOT NULL DEFAULT 'operator',
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        last_login_at DATETIME NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS datasets (
        id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
        filename VARCHAR(255) NOT NULL,
        checksum CHAR(64) NOT NULL UNIQUE,
        total_rows INT UNSIGNED NOT NULL,
        valid_rows INT UNSIGNED NOT NULL DEFAULT 0,
        excluded_rows INT UNSIGNED NOT NULL DEFAULT 0,
        status ENUM('imported','preprocessed','trained','failed') NOT NULL DEFAULT 'imported',
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS opinions (
        id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
        dataset_id BIGINT UNSIGNED NOT NULL,
        source_row INT UNSIGNED NOT NULL,
        external_id VARCHAR(100) NULL,
        source_url TEXT NULL,
        original_text LONGTEXT NOT NULL,
        published_at VARCHAR(100) NULL,
        author_profile_picture TEXT NULL,
        sentiment_label VARCHAR(20) NOT NULL,
        label_reason TEXT NULL,
        label_status VARCHAR(50) NULL,
        preprocessed_text LONGTEXT NULL,
        is_included BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY uq_dataset_row (dataset_id, source_row),
        INDEX idx_opinions_label (sentiment_label),
        CONSTRAINT fk_opinions_dataset FOREIGN KEY (dataset_id)
            REFERENCES datasets(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS training_runs (
        id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
        dataset_id BIGINT UNSIGNED NOT NULL,
        algorithm VARCHAR(100) NOT NULL DEFAULT 'Multinomial Naive Bayes',
        alpha DECIMAL(8,4) NOT NULL DEFAULT 1.0000,
        test_ratio DECIMAL(5,4) NOT NULL,
        random_seed INT NOT NULL DEFAULT 42,
        train_rows INT UNSIGNED NOT NULL,
        test_rows INT UNSIGNED NOT NULL,
        feature_count INT UNSIGNED NOT NULL,
        top_terms JSON NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_training_dataset FOREIGN KEY (dataset_id)
            REFERENCES datasets(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS evaluation_results (
        id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
        training_run_id BIGINT UNSIGNED NOT NULL UNIQUE,
        accuracy DECIMAL(10,8) NOT NULL,
        precision_macro DECIMAL(10,8) NOT NULL,
        recall_macro DECIMAL(10,8) NOT NULL,
        f1_macro DECIMAL(10,8) NOT NULL,
        confusion_matrix JSON NOT NULL,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CONSTRAINT fk_evaluation_training FOREIGN KEY (training_run_id)
            REFERENCES training_runs(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS class_metrics (
        id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
        evaluation_id BIGINT UNSIGNED NOT NULL,
        sentiment_label VARCHAR(20) NOT NULL,
        precision_score DECIMAL(10,8) NOT NULL,
        recall_score DECIMAL(10,8) NOT NULL,
        f1_score DECIMAL(10,8) NOT NULL,
        support_count INT UNSIGNED NOT NULL,
        UNIQUE KEY uq_evaluation_label (evaluation_id, sentiment_label),
        CONSTRAINT fk_metrics_evaluation FOREIGN KEY (evaluation_id)
            REFERENCES evaluation_results(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS prediction_history (
        id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
        training_run_id BIGINT UNSIGNED NOT NULL,
        original_text LONGTEXT NOT NULL,
        preprocessed_text LONGTEXT NOT NULL,
        predicted_label VARCHAR(20) NOT NULL,
        positive_probability DECIMAL(10,8) NOT NULL DEFAULT 0,
        neutral_probability DECIMAL(10,8) NOT NULL DEFAULT 0,
        negative_probability DECIMAL(10,8) NOT NULL DEFAULT 0,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_prediction_created (created_at),
        CONSTRAINT fk_prediction_training FOREIGN KEY (training_run_id)
            REFERENCES training_runs(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
]


class Database:
    def __init__(self, config):
        self.enabled = bool(config.get("MYSQL_ENABLED", True))
        self.host = config["MYSQL_HOST"]
        self.port = config["MYSQL_PORT"]
        self.database = config["MYSQL_DATABASE"]
        self.user = config["MYSQL_USER"]
        self.password = config["MYSQL_PASSWORD"]
        self.available = False
        self.error = None

    def _connection(self, include_database=True):
        options = {
            "host": self.host,
            "port": self.port,
            "user": self.user,
            "password": self.password,
            "charset": "utf8mb4",
            "cursorclass": DictCursor,
            "autocommit": False,
            "connect_timeout": 3,
        }
        if include_database:
            options["database"] = self.database
        return pymysql.connect(**options)

    def initialize(self):
        if not self.enabled:
            return
        if not re.fullmatch(r"[A-Za-z0-9_]+", self.database):
            self.error = "Nama database MySQL tidak valid."
            return
        try:
            connection = self._connection(include_database=False)
            with connection.cursor() as cursor:
                cursor.execute(
                    f"CREATE DATABASE IF NOT EXISTS `{self.database}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
            connection.commit()
            connection.close()
            with self.transaction() as cursor:
                for statement in SCHEMA_STATEMENTS:
                    cursor.execute(statement)
            self.available = True
            self.error = None
        except Exception as exc:
            self.available = False
            self.error = str(exc)

    @contextmanager
    def transaction(self):
        connection = self._connection()
        try:
            with connection.cursor() as cursor:
                yield cursor
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def frame_checksum(frame):
        values = frame[["text", "label"]].fillna("").astype(str)
        payload = values.to_csv(index=False).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def save_dataset(self, frame, filename):
        if not self.available:
            return None
        checksum = self.frame_checksum(frame)
        with self.transaction() as cursor:
            cursor.execute("SELECT id FROM datasets WHERE checksum=%s", (checksum,))
            existing = cursor.fetchone()
            if existing:
                return existing["id"]
            cursor.execute(
                """
                INSERT INTO datasets (filename, checksum, total_rows)
                VALUES (%s, %s, %s)
                """,
                (filename, checksum, len(frame)),
            )
            dataset_id = cursor.lastrowid
            rows = [
                (
                    dataset_id,
                    int(row.source_row),
                    row.external_id or None,
                    row.source_url or None,
                    row.text,
                    row.published_at or None,
                    row.author_profile_picture or None,
                    row.label,
                    row.label_reason or None,
                    row.label_status or None,
                )
                for row in frame.itertuples()
            ]
            cursor.executemany(
                """
                INSERT INTO opinions (
                    dataset_id, source_row, external_id, source_url, original_text,
                    published_at, author_profile_picture, sentiment_label,
                    label_reason, label_status
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                rows,
            )
        return dataset_id

    def ensure_admin(self, name, username, password_hash):
        if not self.available:
            return None
        with self.transaction() as cursor:
            cursor.execute("SELECT id FROM users LIMIT 1")
            existing = cursor.fetchone()
            if existing:
                return existing["id"]
            cursor.execute(
                """
                INSERT INTO users (name, username, password_hash, role)
                VALUES (%s, %s, %s, 'admin')
                """,
                (name, username.lower(), password_hash),
            )
            return cursor.lastrowid

    def find_user_by_username(self, username):
        if not self.available:
            return None
        with self.transaction() as cursor:
            cursor.execute(
                """
                SELECT id, name, username, password_hash, role, is_active
                FROM users WHERE username=%s LIMIT 1
                """,
                (username.lower(),),
            )
            return cursor.fetchone()

    def find_user_by_id(self, user_id):
        if not self.available:
            return None
        with self.transaction() as cursor:
            cursor.execute(
                """
                SELECT id, name, username, role, is_active
                FROM users WHERE id=%s LIMIT 1
                """,
                (user_id,),
            )
            return cursor.fetchone()

    def record_login(self, user_id):
        if not self.available:
            return
        with self.transaction() as cursor:
            cursor.execute(
                "UPDATE users SET last_login_at=NOW() WHERE id=%s", (user_id,)
            )

    def list_users(self):
        if not self.available:
            return []
        with self.transaction() as cursor:
            cursor.execute(
                """
                SELECT id, name, username, role, is_active, last_login_at, created_at
                FROM users ORDER BY created_at DESC, id DESC
                """
            )
            return cursor.fetchall()

    def create_user(self, name, username, password_hash, role):
        if not self.available:
            return None
        with self.transaction() as cursor:
            cursor.execute(
                "SELECT id FROM users WHERE username=%s LIMIT 1",
                (username.lower(),),
            )
            if cursor.fetchone():
                raise ValueError("Username sudah digunakan.")
            cursor.execute(
                """
                INSERT INTO users (name, username, password_hash, role)
                VALUES (%s, %s, %s, %s)
                """,
                (name, username.lower(), password_hash, role),
            )
            return cursor.lastrowid

    def save_preprocessing(self, dataset_id, frame, excluded_count):
        if not self.available or not dataset_id:
            return
        values = [
            (row.preprocessed or None, bool(row.preprocessed), dataset_id, int(row.source_row))
            for row in frame.itertuples()
        ]
        with self.transaction() as cursor:
            cursor.executemany(
                """
                UPDATE opinions SET preprocessed_text=%s, is_included=%s
                WHERE dataset_id=%s AND source_row=%s
                """,
                values,
            )
            cursor.execute(
                """
                UPDATE datasets
                SET valid_rows=%s, excluded_rows=%s, status='preprocessed'
                WHERE id=%s
                """,
                (len(frame) - excluded_count, excluded_count, dataset_id),
            )

    def save_training(self, dataset_id, split, feature_count, top_terms, result):
        if not self.available or not dataset_id:
            return None
        with self.transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO training_runs (
                    dataset_id, test_ratio, random_seed, train_rows, test_rows,
                    feature_count, top_terms
                ) VALUES (%s,%s,42,%s,%s,%s,%s)
                """,
                (
                    dataset_id,
                    split["ratio"],
                    split["train"],
                    split["test"],
                    feature_count,
                    json.dumps(top_terms),
                ),
            )
            training_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO evaluation_results (
                    training_run_id, accuracy, precision_macro, recall_macro,
                    f1_macro, confusion_matrix
                ) VALUES (%s,%s,%s,%s,%s,%s)
                """,
                (
                    training_id,
                    result["accuracy"],
                    result["precision"],
                    result["recall"],
                    result["f1"],
                    json.dumps(result["matrix"]),
                ),
            )
            evaluation_id = cursor.lastrowid
            metrics = []
            for label in ("positif", "netral", "negatif"):
                item = result["report"][label]
                metrics.append(
                    (
                        evaluation_id,
                        label,
                        item["precision"],
                        item["recall"],
                        item["f1-score"],
                        int(item["support"]),
                    )
                )
            cursor.executemany(
                """
                INSERT INTO class_metrics (
                    evaluation_id, sentiment_label, precision_score,
                    recall_score, f1_score, support_count
                ) VALUES (%s,%s,%s,%s,%s,%s)
                """,
                metrics,
            )
            cursor.execute(
                "UPDATE datasets SET status='trained' WHERE id=%s", (dataset_id,)
            )
        return training_id

    def save_prediction(self, training_id, text, processed, label, probabilities):
        if not self.available or not training_id:
            return
        with self.transaction() as cursor:
            cursor.execute(
                """
                INSERT INTO prediction_history (
                    training_run_id, original_text, preprocessed_text,
                    predicted_label, positive_probability, neutral_probability,
                    negative_probability
                ) VALUES (%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    training_id,
                    text,
                    processed,
                    label,
                    probabilities.get("positif", 0),
                    probabilities.get("netral", 0),
                    probabilities.get("negatif", 0),
                ),
            )

    def statistics(self):
        if not self.available:
            return {}
        with self.transaction() as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM datasets")
            datasets = cursor.fetchone()["total"]
            cursor.execute("SELECT COUNT(*) AS total FROM opinions")
            opinions = cursor.fetchone()["total"]
            cursor.execute("SELECT COUNT(*) AS total FROM training_runs")
            trainings = cursor.fetchone()["total"]
            cursor.execute("SELECT COUNT(*) AS total FROM prediction_history")
            predictions = cursor.fetchone()["total"]
            cursor.execute(
                """
                SELECT id, filename, total_rows, valid_rows, status, created_at
                FROM datasets ORDER BY id DESC LIMIT 5
                """
            )
            recent = cursor.fetchall()
        return {
            "datasets": datasets,
            "opinions": opinions,
            "trainings": trainings,
            "predictions": predictions,
            "recent": recent,
        }
