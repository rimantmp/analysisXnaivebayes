# Analisis Sentimen Pinjol

Aplikasi web Flask untuk menganalisis sentimen opini masyarakat tentang
pinjaman online pada media sosial X menggunakan TF-IDF dan Multinomial Naive
Bayes.

## Menjalankan aplikasi

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run.py
```

Buka `http://127.0.0.1:5000`. File `Dataset.xlsx` otomatis dimuat saat halaman
import dibuka. Dataset pengganti harus berformat `.xlsx` dan memiliki kolom
`text` serta `sentimen` (atau `label`).

## Login

Seluruh halaman analisis dilindungi oleh login berbasis session Flask. Saat
database belum memiliki pengguna, aplikasi membuat satu akun admin dari
environment variable berikut:

```powershell
$env:ADMIN_NAME="Administrator"
$env:ADMIN_USERNAME="admin"
$env:ADMIN_PASSWORD="password-yang-kuat"
$env:SECRET_KEY="kunci-session-acak-dan-panjang"
python run.py
```

Jika environment variable belum diatur, akun awal pengembangan adalah
`admin` dengan password `admin123`. Ganti nilai tersebut sebelum aplikasi
digunakan di jaringan atau lingkungan produksi.

Admin dapat membuka menu **Manajemen Akun** untuk membuat pengguna baru dengan
role `admin` atau `operator`. Operator dapat menggunakan fitur analisis, tetapi
tidak dapat membuka halaman administrasi akun.

Jika eksekusi script PowerShell dibatasi, aplikasi tetap dapat dijalankan tanpa
aktivasi:

```powershell
.\.venv\Scripts\python.exe run.py
```

## Alur penggunaan

1. Import dan validasi dataset.
2. Jalankan preprocessing.
3. Periksa distribusi dan validitas label.
4. Bentuk matriks TF-IDF.
5. Latih model dengan pembagian data stratified.
6. Lihat evaluasi, dashboard, dan gunakan prediksi teks baru.

## MySQL

Konfigurasi MySQL tersedia melalui environment variable `MYSQL_HOST`,
`MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, dan `MYSQL_PASSWORD`. Nilai
default ditujukan untuk MySQL lokal:

```powershell
$env:MYSQL_HOST="127.0.0.1"
$env:MYSQL_PORT="3306"
$env:MYSQL_DATABASE="sentiment_pinjol"
$env:MYSQL_USER="root"
$env:MYSQL_PASSWORD=""
python run.py
```

Saat aplikasi dimulai, database dan tabel dibuat otomatis. Data yang disimpan:

- metadata dataset dan seluruh opini;
- hasil preprocessing setiap opini;
- parameter dan riwayat pelatihan;
- hasil evaluasi serta metrik per kelas;
- riwayat prediksi teks baru.

Status koneksi dan jumlah data dapat diperiksa melalui menu **Database**.
Objek model dan matriks TF-IDF tetap berada di memori karena tidak cocok
disimpan sebagai baris relasional.

## Pengujian

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```
