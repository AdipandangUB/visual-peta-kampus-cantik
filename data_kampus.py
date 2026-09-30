"""
Data bersama untuk aplikasi Peta Kampus Cantik dan skrip pembuat gambar contoh.
Berisi daftar universitas (dari berkas "Lokasi Universitas.docx"), preset gaya,
dan fungsi bantu kecil. Tidak memakai Streamlit agar bisa diimpor skrip mana pun.
"""

import re
import unicodedata
from typing import Any

# ---------------------------------------------------------------------------
# Data lokasi universitas (dari berkas "Lokasi Universitas.docx")
# Format: nama lengkap, singkatan, latitude, longitude, radius awal (meter).
# Radius awal adalah PERKIRAAN kasar agar area kampus utama kurang lebih tercakup;
# sesuaikan bila perlu lewat slider di aplikasi (koordinat belum tentu tepat di pusat kampus).
# ---------------------------------------------------------------------------
UNIVERSITAS = [
    {"nama": "Universitas Brawijaya", "singkatan": "UB", "lat": -7.9524597, "lon": 112.6111021, "radius": 800},
    {"nama": "Universitas Indonesia", "singkatan": "UI", "lat": -6.3613844, "lon": 106.822841, "radius": 1800},
    {"nama": "Institut Teknologi Bandung", "singkatan": "ITB", "lat": -6.893408, "lon": 107.607505, "radius": 600},
    {"nama": "Universitas Gadjah Mada", "singkatan": "UGM", "lat": -7.7716364, "lon": 110.3773275, "radius": 1400},
    {"nama": "IPB University", "singkatan": "IPB", "lat": -6.5561909, "lon": 106.7199156, "radius": 1500},
    {"nama": "Universitas Padjadjaran", "singkatan": "Unpad", "lat": -6.9245846, "lon": 107.7666021, "radius": 1200},
    {"nama": "Universitas Diponegoro", "singkatan": "Undip", "lat": -7.0519625, "lon": 110.4383113, "radius": 1500},
    {"nama": "Universitas Sebelas Maret", "singkatan": "UNS", "lat": -7.5594932, "lon": 110.8432734, "radius": 900},
    {"nama": "Institut Teknologi Sepuluh Nopember", "singkatan": "ITS", "lat": -7.2810536, "lon": 112.7846819, "radius": 1200},
    {"nama": "Universitas Airlangga", "singkatan": "Unair", "lat": -7.2672541, "lon": 112.781301, "radius": 800},
    {"nama": "Universitas Hasanuddin", "singkatan": "Unhas", "lat": -5.1332416, "lon": 119.4821689, "radius": 1500},
    {"nama": "Universitas Sam Ratulangi", "singkatan": "Unsrat", "lat": 1.4582984, "lon": 124.8248965, "radius": 1000},
    {"nama": "Universitas Syiah Kuala", "singkatan": "USK", "lat": 5.5684614, "lon": 95.3655648, "radius": 1000},
    {"nama": "Institut Teknologi Kalimantan", "singkatan": "ITK", "lat": -1.1499495, "lon": 116.8576775, "radius": 1200},
    {"nama": "Institut Teknologi Sumatera", "singkatan": "ITERA", "lat": -5.3602126, "lon": 105.300363, "radius": 1500},
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
