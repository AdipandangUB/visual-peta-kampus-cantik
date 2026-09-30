"""
Data bersama untuk aplikasi Peta Kampus Cantik dan skrip pembuat gambar contoh.
Berisi daftar universitas (koordinat dari tautan OSM pada berkas "Lokasi Universitas.docx"), preset gaya,
dan fungsi bantu kecil. Tidak memakai Streamlit agar bisa diimpor skrip mana pun.
"""

import re
import unicodedata
from typing import Any

# ---------------------------------------------------------------------------
# Data lokasi universitas
# Sumber koordinat: tautan OpenStreetMap pada berkas "Lokasi Universitas.docx"
# (bagian #map=zoom/lintang/bujur = titik tengah peta yang dipilih pengguna).
# Koordinat lama pada berkas (kolom "lintang; bujur") tidak lagi dipakai.
# Format: nama lengkap, singkatan, lat, lon, radius awal (meter), tautan OSM.
# Radius awal adalah PERKIRAAN kasar agar area kampus utama kurang lebih tercakup;
# sesuaikan bila perlu lewat slider di aplikasi.
# ---------------------------------------------------------------------------
UNIVERSITAS = [
    {"nama": "Universitas Brawijaya", "singkatan": "UB", "lat": -7.95191, "lon": 112.61453, "radius": 800, "osm": "https://www.openstreetmap.org/#map=16/-7.95191/112.61453"},
    {"nama": "Universitas Indonesia", "singkatan": "UI", "lat": -6.36124, "lon": 106.83037, "radius": 1800, "osm": "https://www.openstreetmap.org/#map=15/-6.36124/106.83037"},
    {"nama": "Institut Teknologi Bandung", "singkatan": "ITB", "lat": -6.890949, "lon": 107.611063, "radius": 600, "osm": "https://www.openstreetmap.org/#map=17/-6.890949/107.611063"},
    {"nama": "Universitas Gadjah Mada", "singkatan": "UGM", "lat": -7.76948, "lon": 110.37902, "radius": 1400, "osm": "https://www.openstreetmap.org/#map=16/-7.76948/110.37902"},
    {"nama": "IPB University", "singkatan": "IPB", "lat": -6.55530, "lon": 106.72411, "radius": 1500, "osm": "https://www.openstreetmap.org/#map=15/-6.55530/106.72411"},
    {"nama": "Universitas Padjadjaran", "singkatan": "Unpad", "lat": -6.92413, "lon": 107.77313, "radius": 1200, "osm": "https://www.openstreetmap.org/#map=15/-6.92413/107.77313"},
    {"nama": "Universitas Diponegoro", "singkatan": "Undip", "lat": -7.05089, "lon": 110.43873, "radius": 1500, "osm": "https://www.openstreetmap.org/#map=16/-7.05089/110.43873"},
    {"nama": "Universitas Sebelas Maret", "singkatan": "UNS", "lat": -7.55959, "lon": 110.85317, "radius": 900, "osm": "https://www.openstreetmap.org/#map=16/-7.55959/110.85317"},
    {"nama": "Institut Teknologi Sepuluh Nopember", "singkatan": "ITS", "lat": -7.28270, "lon": 112.79530, "radius": 1200, "osm": "https://www.openstreetmap.org/#map=16/-7.28270/112.79530"},
    {"nama": "Universitas Airlangga", "singkatan": "Unair", "lat": -7.26736, "lon": 112.75543, "radius": 800, "osm": "https://www.openstreetmap.org/#map=16/-7.26736/112.75543"},
]
UNIV_BY_NAMA = {u["nama"]: u for u in UNIVERSITAS}

# ---------------------------------------------------------------------------
# Preset gaya (diambil dari contoh bawaan prettymapp, tanpa alamat)
# custom_title dikosongkan -> judul peta otomatis memakai singkatan kampus.
# ---------------------------------------------------------------------------
PRESET = {
    "Peach — bulat": {
        "custom_title": "", "radius": 1100, "style": "Peach", "shape": "circle",
        "contour_width": 1, "contour_color": "#2F3537", "name_on": True,
        "font_size": 25, "font_color": "#2F3737", "text_x": 19, "text_y": -45,
        "text_rotation": -24, "bg_shape": "circle", "bg_buffer": 2,
        "bg_color": "#F2F4CB",
    },
    "Auburn — persegi": {
        "custom_title": "", "radius": 640, "style": "Auburn", "shape": "rectangle",
        "contour_width": 0, "contour_color": "#2F3538", "name_on": True,
        "font_size": 30, "font_color": "#2F3738", "text_x": -53, "text_y": 18,
        "text_rotation": -90, "bg_shape": "rectangle", "bg_buffer": 6,
        "bg_color": "#F9EFDC",
    },
    "Citrus — kontur putih": {
        "custom_title": "", "radius": 1020, "style": "Citrus", "shape": "circle",
        "contour_width": 15, "contour_color": "#FFFFFF", "name_on": True,
        "font_size": 25, "font_color": "#FFFFFF", "text_x": -41, "text_y": 25,
        "text_rotation": -46, "bg_shape": None, "bg_buffer": 4,
        "bg_color": "#000000",
    },
    "Flannel — persegi": {
        "custom_title": "", "radius": 650, "style": "Flannel", "shape": "rectangle",
        "contour_width": 0, "contour_color": "#2F3737", "name_on": True,
        "font_size": 27, "font_color": "#2F3737", "text_x": 0, "text_y": -33,
        "text_rotation": 0, "bg_shape": "rectangle", "bg_buffer": 0,
        "bg_color": "#EDEFDA",
    },
    "Peach — tanpa judul": {
        "custom_title": "", "radius": 850, "style": "Peach", "shape": "circle",
        "contour_width": 0, "contour_color": "#2F3737", "name_on": False,
        "font_size": 16, "font_color": "#2F3737", "text_x": -37, "text_y": 26,
        "text_rotation": -45, "bg_shape": "rectangle", "bg_buffer": 2,
        "bg_color": "#F2F4CB",
    },
}
PRESET_NAMES = list(PRESET.keys())

# Setiap kampus diberi satu preset gaya sebagai tampilan awal (bergilir dari
# empat preset pertama). Gambar contoh di example_prints/ dibuat dengan preset ini.
PRESET_GALERI = PRESET_NAMES[:4]


def preset_untuk(nama_kampus: str) -> str:
    idx = [u["nama"] for u in UNIVERSITAS].index(nama_kampus)
    return PRESET_GALERI[idx % len(PRESET_GALERI)]


def slugify(value: Any) -> str:
    """Ubah teks menjadi nama berkas yang aman (huruf kecil, tanda hubung)."""
    value = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")
