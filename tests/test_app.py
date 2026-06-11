import io

import pandas as pd
from werkzeug.security import generate_password_hash

from app import create_app
from app.services.ml import FeatureExtractor, NaiveBayesClassifier, evaluate
from app.services.preprocessor import TextPreprocessor
from app.services.store import store


def sample_frame():
    rows = []
    samples = {
        "positif": ["pinjol membantu kebutuhan dana", "layanan pinjaman sangat membantu"],
        "netral": ["informasi cicilan pinjaman online", "aturan pinjol terbaru diumumkan"],
        "negatif": ["teror pinjol sangat meresahkan", "bunga pinjaman sangat mencekik"],
    }
    for label, texts in samples.items():
        for text in texts:
            rows.append({"text": text, "sentimen": label})
    return pd.DataFrame(rows)


def test_preprocessor_removes_noise():
    result = TextPreprocessor().preprocess(
        "INFO @akun https://contoh.id #Pinjol 123 sangat MEMBANTU!!!"
    )
    assert "http" not in result
    assert "123" not in result
    assert result == result.lower()
    assert result


def test_ml_services_return_valid_result():
    documents = [
        "bantu dana cepat",
        "bantu butuh dana",
        "informasi cicil pinjam",
        "aturan cicil pinjam",
        "teror bunga tinggi",
        "tagih teror tinggi",
    ]
    labels = ["positif", "positif", "netral", "netral", "negatif", "negatif"]
    extractor = FeatureExtractor()
    matrix = extractor.fit_transform(documents)
    classifier = NaiveBayesClassifier()
    classifier.train(matrix, labels)
    predictions = classifier.predict(matrix)
    result = evaluate(labels, predictions)
    assert matrix.shape[0] == 6
    assert 0 <= result["accuracy"] <= 1
    assert sum(map(sum, result["matrix"])) == 6


def test_full_route_pipeline():
    store.reset()
    app = create_app({"TESTING": True, "DEFAULT_DATASET": "missing.xlsx"})
    client = app.test_client()
    output = io.BytesIO()
    sample_frame().to_excel(output, index=False)
    output.seek(0)

    response = client.post(
        "/import",
        data={"dataset": (output, "sample.xlsx")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200
    assert b"6 baris" in response.data
    assert client.get("/preprocessing").status_code == 200
    assert client.get("/labels").status_code == 200
    assert client.get("/tfidf").status_code == 200
    assert client.get("/classification").status_code == 200
    assert client.get("/evaluation").status_code == 200
    assert client.get("/dashboard").status_code == 200
    assert client.get("/database").status_code == 200

    response = client.post("/prediction", data={"text": "pinjol sangat membantu"})
    assert response.status_code == 200
    assert b"Hasil prediksi" in response.data


class FakeAuthDatabase:
    available = True
    database = "test_database"
    error = None

    def __init__(self):
        self.user = {
            "id": 1,
            "name": "Administrator",
            "username": "admin",
            "password_hash": generate_password_hash("rahasia123"),
            "role": "admin",
            "is_active": True,
        }
        self.created_users = []

    def find_user_by_username(self, username):
        return self.user if username == self.user["username"] else None

    def find_user_by_id(self, user_id):
        if user_id != self.user["id"]:
            return None
        return {key: value for key, value in self.user.items() if key != "password_hash"}

    def record_login(self, user_id):
        return None

    def list_users(self):
        return [
            {
                "id": self.user["id"],
                "name": self.user["name"],
                "username": self.user["username"],
                "role": self.user["role"],
                "is_active": self.user["is_active"],
                "last_login_at": None,
                "created_at": "2026-06-11",
            },
            *self.created_users,
        ]

    def create_user(self, name, username, password_hash, role):
        if username == self.user["username"]:
            raise ValueError("Username sudah digunakan.")
        new_user = {
            "id": len(self.created_users) + 2,
            "name": name,
            "username": username,
            "role": role,
            "is_active": True,
            "last_login_at": None,
            "created_at": "2026-06-11",
        }
        self.created_users.append(new_user)
        return new_user["id"]


def test_login_protects_routes_and_logout_clears_session():
    app = create_app(
        {
            "TESTING": True,
            "MYSQL_ENABLED": False,
            "AUTH_DISABLED": False,
            "DEFAULT_DATASET": "missing.xlsx",
        }
    )
    app.extensions["database"] = FakeAuthDatabase()
    client = app.test_client()

    response = client.get("/import")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]

    response = client.post(
        "/login", data={"username": "admin", "password": "salah"}
    )
    assert b"Username atau password tidak benar" in response.data

    response = client.post(
        "/login",
        data={"username": "admin", "password": "rahasia123"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/import")

    assert client.get("/import").status_code == 200
    response = client.post("/logout", follow_redirects=True)
    assert b"Anda telah keluar dari aplikasi" in response.data
    assert b"Selamat datang" in response.data


def test_admin_can_create_user_and_operator_is_forbidden():
    app = create_app(
        {
            "TESTING": True,
            "MYSQL_ENABLED": False,
            "AUTH_DISABLED": False,
            "DEFAULT_DATASET": "missing.xlsx",
        }
    )
    database = FakeAuthDatabase()
    app.extensions["database"] = database
    client = app.test_client()

    client.post("/login", data={"username": "admin", "password": "rahasia123"})
    response = client.post(
        "/admin/users",
        data={
            "name": "Operator Analisis",
            "username": "operator.analisis",
            "role": "operator",
            "password": "password123",
            "password_confirmation": "password123",
        },
        follow_redirects=True,
    )
    assert b"Akun operator.analisis berhasil dibuat" in response.data
    assert b"Operator Analisis" in response.data
    assert database.created_users[0]["role"] == "operator"

    database.user["role"] = "operator"
    response = client.get("/admin/users")
    assert response.status_code == 403
    assert b"Akses ditolak" in response.data
