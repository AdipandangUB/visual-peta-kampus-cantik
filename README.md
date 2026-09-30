# Peta Kampus Cantik — Universitas di Indonesia

Aplikasi Streamlit berbahasa Indonesia (adaptasi dari [prettymapp](https://github.com/chrieke/prettymapp), MIT).

## Struktur berkas
- `app.py` — aplikasi Streamlit
- `data_kampus.py` — daftar 15 universitas + preset gaya
- `generate_contoh.py` — pembuat gambar galeri
- `requirements.txt`
- `example_prints/` — gambar galeri (dibuat oleh `generate_contoh.py`)

## Langkah
1. Di komputer Anda: `pip install prettymapp pyogrio`, lalu `python generate_contoh.py`.
2. Commit seluruh berkas, termasuk folder `example_prints/`, ke GitHub.
3. Di Streamlit Cloud, *Main file path* = `app.py`; pilih Python 3.11/3.12.
