# PISCA

Personal Intelligent Study & Chat Assistant adalah MVP chatbot web lokal. Jawaban AI dibuat oleh Ollama di komputer Anda, sedangkan memory dan riwayat chat disimpan dalam SQLite. Tidak ada API AI cloud.

## Kebutuhan

- Windows 10/11
- Python 3.11 atau lebih baru
- [Ollama](https://ollama.com/) dan model lokal yang sudah diunduh

## Instalasi Windows

Jalankan PowerShell dari folder project:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Instal Ollama, lalu unduh model yang sama dengan `LLM_MODEL` pada `.env`:

```powershell
ollama pull llama3.2:3b
ollama serve
```

Pada terminal PowerShell kedua, aktifkan virtual environment bila belum aktif lalu jalankan:

```powershell
python -m uvicorn backend.main:app --reload
```

Buka `http://127.0.0.1:8000` di browser. Endpoint kesehatan tersedia pada `http://127.0.0.1:8000/health`.

## Penggunaan Memory

- Ketik `Ingat bahwa nama saya Pisca` untuk menyimpan informasi eksplisit.
- Ketik `Ingat bahwa saya mahasiswa Sistem Informasi` untuk menyimpan status/jurusan.
- Ketik `Lupakan bahwa saya mahasiswa Sistem Informasi` untuk menghapusnya.
- Gunakan panel **Memory** untuk menambah, mengubah, atau menghapus memory secara manual.

PISCA tidak menyimpan semua pesan sebagai memory. Memory hanya berasal dari perintah eksplisit atau pengelolaan melalui panel.

## Konfigurasi

Semua konfigurasi model berada di `.env`:

```env
# none = retrieval-only (dataset + memory), tanpa model, cocok untuk Render free tier
# ollama = pakai Ollama lokal untuk jawaban generatif
LLM_PROVIDER=none
LLM_MODEL=llama3.2:3b
LLM_BASE_URL=http://localhost:11434
```

Default PISCA adalah `none`: jawaban diambil langsung dari dataset dan memory tanpa model, sehingga tetap berjalan tanpa Ollama. Untuk mengaktifkan jawaban generatif, ganti `LLM_PROVIDER=ollama` lalu jalankan `ollama serve`.

`backend/services/llm_service.py` menyediakan abstraksi `LLMService`. Business logic chat tidak bergantung langsung pada Ollama sehingga runtime lain, termasuk Android pada masa depan, dapat ditambahkan tanpa mengubah layanan chat dan memory.

## Dataset

`data/pisca_dataset.jsonl` berisi 100 contoh tanya-jawab dalam 10 kategori. Dataset ini merupakan file JSON Lines: satu objek JSON per baris. Tambahkan data dengan field `category`, `instruction`, dan `response`.

Dataset dipakai langsung oleh alur chat:

- Pertanyaan yang sama persis dengan dataset dijawab langsung dari jawaban dataset.
- Pertanyaan yang mirip dicari secara offline berdasarkan kemiripan kata, lalu referensinya dikirim ke Ollama agar dijelaskan secara natural.
- Pertanyaan tanpa referensi dataset tetap dapat dijawab Ollama menggunakan pengetahuan model lokal.
- Memory pengguna tetap dipisahkan dari dataset dan diprioritaskan untuk pertanyaan pribadi.

Validasi dataset:

```powershell
python scripts/validate_dataset.py
```

Validator memeriksa JSON, field wajib, nilai kosong, jumlah baris, dan pertanyaan duplikat sederhana.

## Testing

```powershell
pytest
```

Tes mencakup koneksi/CRUD SQLite melalui endpoint memory, penyimpanan memory dari chat eksplisit, endpoint health, dan validator dataset. LLM tidak dipanggil untuk tes chat eksplisit.

## Struktur

```text
backend/       FastAPI, model SQLite, route, service, dan prompt
frontend/      UI HTML/CSS/JavaScript vanilla
scripts/       Inisialisasi database dan validasi dataset
```

## Deploy ke Render

PISCA dapat di-deploy ke Render free tier menggunakan mode retrieval-only (`LLM_PROVIDER=none`).

1. Push project ke repository GitHub.
2. Di Render, pilih **New > Web Service** lalu hubungkan repository.
3. Render otomatis membaca `render.yaml`, atau isi manual:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - Environment variable: `LLM_PROVIDER=none`
4. Setelah deploy, buka URL Render yang diberikan.

Catatan: SQLite di Render free tier bersifat ephemeral, jadi data memory dan chat bisa ter-reset saat deploy ulang. Untuk data permanen, upgrade ke PostgreSQL Render lalu set `DATABASE_URL` ke URL PostgreSQL.

## Troubleshooting

- **Local AI model belum tersedia**: jalankan `ollama serve`, pastikan `LLM_BASE_URL` benar, lalu gunakan `ollama list` untuk memeriksa model.
- **Model tidak ditemukan**: unduh dengan `ollama pull <nama-model>` dan samakan `LLM_MODEL` pada `.env`.
- **Database tidak dapat diakses**: pastikan folder `data` dapat ditulis dan tidak dikunci aplikasi lain.
- **PowerShell menolak aktivasi venv**: jalankan `Set-ExecutionPolicy -Scope Process Bypass`, lalu ulangi aktivasi environment.
