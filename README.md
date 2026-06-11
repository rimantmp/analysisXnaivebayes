# Analisis Sentimen Pinjaman Online pada Media Sosial X

Aplikasi web untuk menganalisis sentimen opini masyarakat mengenai dampak
pinjaman online pada media sosial X. Sistem dibangun menggunakan Flask,
preprocessing bahasa Indonesia, TF-IDF, dan algoritma Multinomial Naive Bayes.

Aplikasi menyediakan alur analisis lengkap mulai dari impor dataset,
preprocessing, validasi label, ekstraksi fitur, pelatihan model, evaluasi,
dashboard visualisasi, hingga prediksi teks baru.

## Fitur Utama

- Login dan logout berbasis session Flask.
- Konfirmasi sebelum logout.
- Role pengguna `admin` dan `operator`.
- Manajemen akun khusus admin.
- Import dataset Excel `.xlsx`.
- Validasi kolom, ukuran dataset, dan label sentimen.
- Preprocessing teks bahasa Indonesia.
- Ekstraksi fitur TF-IDF unigram dan bigram.
- Klasifikasi Multinomial Naive Bayes.
- Stratified train-test split.
- Evaluasi accuracy, macro precision, macro recall, dan macro F1-score.
- Confusion matrix dan metrik setiap kelas.
- Dashboard distribusi sentimen dan kata dominan.
- Prediksi sentimen teks baru beserta probabilitas setiap kelas.
- Penyimpanan permanen ke MySQL.
- Tampilan Material Design rounded dan responsif.

## Teknologi

| Komponen | Teknologi |
|---|---|
| Backend | Python, Flask |
| Template | Jinja2 |
| Database | MySQL 8, PyMySQL |
| Pengolahan data | pandas, NumPy |
| Machine learning | scikit-learn |
| Preprocessing Indonesia | PySastrawi |
| File Excel | openpyxl |
| Tampilan | Tailwind CSS melalui CDN |
| Grafik | Chart.js melalui CDN |
| Pengujian | pytest |

## Alur Analisis

```text
Import Dataset
      |
      v
Preprocessing Teks
      |
      v
Validasi Label
      |
      v
Ekstraksi TF-IDF
      |
      v
Stratified Train-Test Split
      |
      v
Multinomial Naive Bayes
      |
      v
Evaluasi dan Dashboard
      |
      v
Prediksi Teks Baru
```

## Preprocessing Teks

Pipeline preprocessing menjalankan tahapan berikut:

1. Menghapus URL.
2. Menghapus mention.
3. Mengubah hashtag menjadi kata biasa.
4. Menghapus angka dan karakter nonalfabet.
5. Case folding menjadi huruf kecil.
6. Tokenisasi berdasarkan spasi.
7. Menghapus stopword bahasa Indonesia dan kata informal tambahan.
8. Stemming menggunakan PySastrawi.
9. Mengeluarkan dokumen yang menjadi kosong setelah preprocessing.

## Persyaratan Sistem

- Windows 10/11, Linux, atau macOS.
- Python 3.10 atau lebih baru.
- MySQL 8 atau kompatibel.
- Koneksi internet ketika membuka aplikasi untuk memuat Tailwind CSS dan
  Chart.js dari CDN.
- Git bersifat opsional, tetapi disarankan untuk version control.

## Instalasi Windows

### 1. Clone atau buka proyek

Jika repository sudah tersedia di GitHub:

```powershell
git clone https://github.com/rimantmp/analysisXnaivebayes.git
cd analysisXnaivebayes
```

Jika proyek sudah ada di komputer, buka terminal pada folder proyek.

### 2. Buat virtual environment

```powershell
python -m venv .venv
```

Aktifkan virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Jika PowerShell menolak eksekusi script:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Alternatif tanpa aktivasi:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe run.py
```

### 3. Instal dependency

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Siapkan MySQL

Pastikan service MySQL aktif. Konfigurasi default aplikasi:

```text
Host     : 127.0.0.1
Port     : 3306
Database : sentiment_pinjol
User     : root
Password : kosong
```

Database dan seluruh tabel akan dibuat otomatis ketika aplikasi dimulai,
selama pengguna MySQL memiliki izin `CREATE DATABASE` dan `CREATE TABLE`.

### 5. Atur environment variable

Contoh konfigurasi tersedia pada `.env.example`. Aplikasi saat ini membaca
environment variable sistem secara langsung.

PowerShell:

```powershell
$env:MYSQL_ENABLED="true"
$env:MYSQL_HOST="127.0.0.1"
$env:MYSQL_PORT="3306"
$env:MYSQL_DATABASE="sentiment_pinjol"
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD=""

$env:SECRET_KEY="ganti-dengan-rangkaian-acak-yang-panjang"
$env:ADMIN_NAME="Administrator"
$env:ADMIN_USERNAME="admin"
$env:ADMIN_PASSWORD="password-admin-yang-kuat"
```

Environment variable hanya berlaku pada terminal aktif. Jalankan aplikasi
pada terminal yang sama.

### 6. Jalankan aplikasi

```powershell
python run.py
```

Buka:

```text
http://127.0.0.1:5000
```

## Akun Awal

Saat tabel `users` masih kosong, aplikasi membuat satu akun admin dari
environment variable:

```text
ADMIN_NAME
ADMIN_USERNAME
ADMIN_PASSWORD
```

Jika environment variable belum diatur, kredensial pengembangan adalah:

```text
Username : admin
Password : admin123
```

> Ganti `ADMIN_PASSWORD` dan `SECRET_KEY` sebelum aplikasi digunakan pada
> jaringan lokal, server, atau lingkungan produksi.

Akun awal hanya dibuat ketika tabel pengguna masih kosong. Mengubah
`ADMIN_PASSWORD` setelah akun terbentuk tidak otomatis mengganti password akun
yang sudah tersimpan.

## Hak Akses

### Admin

- Mengakses seluruh pipeline analisis.
- Melihat status database.
- Membuat akun admin atau operator.
- Melihat daftar pengguna.

### Operator

- Mengakses pipeline analisis.
- Melakukan prediksi teks.
- Melihat evaluasi dan dashboard.
- Tidak dapat mengakses halaman manajemen akun.

Percobaan operator membuka `/admin/users` menghasilkan respons HTTP `403`.

## Format Dataset

Dataset wajib berupa file `.xlsx` dengan maksimal 50.000 baris.

Kolom wajib:

| Kolom | Keterangan |
|---|---|
| `text` | Teks opini atau posting |
| `sentimen` | Label `positif`, `netral`, atau `negatif` |

Nama `label` juga diterima sebagai pengganti `sentimen`.

Kolom opsional yang ikut disimpan jika tersedia:

| Kolom | Keterangan |
|---|---|
| `id` | ID posting |
| `url` | URL posting |
| `createdAt` | Waktu publikasi |
| `author.profilePicture` | URL gambar profil |
| `alasan` | Alasan pemberian label |
| `status_label` | Status proses pelabelan |

Contoh:

| text | sentimen |
|---|---|
| Pinjaman online membantu kebutuhan mendesak | positif |
| Informasi mengenai aturan pinjaman online terbaru | netral |
| Bunga dan teror penagihan sangat meresahkan | negatif |

File `Dataset.xlsx` pada root proyek otomatis dimuat ketika halaman import
dibuka untuk pertama kali.

## Penggunaan Aplikasi

### 1. Login

Masukkan username dan password. Seluruh halaman selain login memerlukan session
pengguna aktif.

### 2. Import Dataset

Unggah file `.xlsx` atau gunakan `Dataset.xlsx` bawaan. Sistem akan:

- memeriksa kolom wajib;
- menolak file kosong;
- membatasi jumlah baris;
- menghitung distribusi label;
- menyimpan metadata dan opini ke MySQL.

### 3. Preprocessing

Jalankan preprocessing untuk membuat kolom teks bersih. Data kosong setelah
preprocessing dikeluarkan dari proses klasifikasi dan dihitung sebagai data
yang dikecualikan.

### 4. Validasi Label

Pastikan semua label termasuk dalam:

```text
positif
netral
negatif
```

Klasifikasi diblokir jika masih ada label tidak valid.

### 5. Ekstraksi TF-IDF

Sistem membentuk matriks TF-IDF dengan konfigurasi utama:

```text
ngram_range = (1, 2)
min_df      = 2
max_features = 10000
```

Halaman menampilkan ukuran matriks dan 20 istilah dengan rata-rata bobot
TF-IDF tertinggi.

### 6. Klasifikasi

Pilih proporsi data uji 20% atau 30%. Sistem menggunakan:

- `MultinomialNB`;
- Laplace smoothing `alpha=1.0`;
- stratified split;
- random seed `42`.

Jumlah data uji otomatis disesuaikan pada dataset kecil agar setiap kelas dapat
terwakili.

### 7. Evaluasi

Metrik yang ditampilkan:

- accuracy;
- macro precision;
- macro recall;
- macro F1-score;
- confusion matrix;
- precision, recall, F1-score, dan support setiap kelas.

Macro average digunakan agar evaluasi tetap memperhatikan kelas minoritas pada
dataset yang tidak seimbang.

### 8. Dashboard

Dashboard menampilkan:

- total opini;
- distribusi positif, netral, dan negatif;
- grafik distribusi sentimen;
- grafik performa model;
- kata dominan setiap kelas.

### 9. Prediksi

Masukkan satu teks opini baru. Sistem menampilkan:

- hasil preprocessing;
- label prediksi;
- probabilitas positif;
- probabilitas netral;
- probabilitas negatif.

Hasil prediksi disimpan ke tabel `prediction_history`.

## Database

Schema MySQL menggunakan database default `sentiment_pinjol`.

| Tabel | Fungsi |
|---|---|
| `users` | Akun, password hash, role, status, dan waktu login |
| `datasets` | Metadata file dan status pipeline |
| `opinions` | Teks asli, metadata sumber, label, dan hasil preprocessing |
| `training_runs` | Parameter dan metadata pelatihan |
| `evaluation_results` | Metrik global dan confusion matrix |
| `class_metrics` | Metrik setiap kelas |
| `prediction_history` | Riwayat prediksi teks baru |

Password tidak disimpan sebagai teks biasa. Aplikasi menggunakan password hash
dari Werkzeug.

Objek classifier, vectorizer, dan matriks TF-IDF masih disimpan di memori
aplikasi. Karena itu, setelah server dimulai ulang, tahapan TF-IDF dan
klasifikasi perlu dijalankan kembali sebelum fitur prediksi digunakan.

## Endpoint

| Method | Endpoint | Fungsi |
|---|---|---|
| GET, POST | `/login` | Login pengguna |
| POST | `/logout` | Logout pengguna |
| GET | `/` | Redirect ke halaman import |
| GET, POST | `/import` | Import dan pratinjau dataset |
| GET, POST | `/preprocessing` | Menjalankan preprocessing |
| GET | `/labels` | Validasi dan distribusi label |
| GET, POST | `/tfidf` | Ekstraksi fitur |
| GET, POST | `/classification` | Split dan training model |
| GET | `/evaluation` | Evaluasi model |
| GET | `/dashboard` | Visualisasi hasil |
| GET, POST | `/prediction` | Prediksi teks baru |
| GET | `/database` | Status dan statistik database |
| GET, POST | `/admin/users` | Manajemen akun khusus admin |

## Struktur Proyek

```text
.
|-- app/
|   |-- __init__.py
|   |-- auth.py
|   |-- config.py
|   |-- web.py
|   |-- services/
|   |   |-- database.py
|   |   |-- ml.py
|   |   |-- preprocessor.py
|   |   `-- store.py
|   `-- templates/
|       |-- base.html
|       |-- login.html
|       |-- users.html
|       |-- import.html
|       |-- preprocessing.html
|       |-- labels.html
|       |-- tfidf.html
|       |-- classification.html
|       |-- evaluation.html
|       |-- dashboard.html
|       |-- prediction.html
|       |-- database.html
|       `-- 403.html
|-- tests/
|   `-- test_app.py
|-- Dataset.xlsx
|-- requirements.txt
|-- run.py
|-- .env.example
`-- README.md
```

## Konfigurasi

| Variable | Default | Keterangan |
|---|---|---|
| `SECRET_KEY` | `dev-sentiment-pinjol` | Kunci session Flask |
| `MYSQL_ENABLED` | `true` | Mengaktifkan integrasi MySQL |
| `MYSQL_HOST` | `127.0.0.1` | Host MySQL |
| `MYSQL_PORT` | `3306` | Port MySQL |
| `MYSQL_DATABASE` | `sentiment_pinjol` | Nama database |
| `MYSQL_USER` | `root` | Pengguna MySQL |
| `MYSQL_PASSWORD` | kosong | Password MySQL |
| `ADMIN_NAME` | `Administrator` | Nama akun awal |
| `ADMIN_USERNAME` | `admin` | Username akun awal |
| `ADMIN_PASSWORD` | `admin123` | Password akun awal |
| `AUTH_DISABLED` | `false` | Menonaktifkan auth, hanya untuk test |

## Pengujian

Jalankan seluruh pengujian:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Pengujian mencakup:

- preprocessing teks;
- service TF-IDF dan Naive Bayes;
- alur route lengkap;
- proteksi halaman tanpa login;
- login dengan password valid dan tidak valid;
- logout dan penghapusan session;
- pembuatan pengguna oleh admin;
- penolakan akses manajemen akun untuk operator.
