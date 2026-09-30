"""
Peta Kampus Cantik — Universitas di Indonesia
=============================================
Aplikasi Streamlit untuk membuat peta artistik dari data OpenStreetMap
(OSM) di sekitar kampus-kampus universitas di Indonesia.
"""

import copy
import io
from io import StringIO
from pathlib import Path

import streamlit as st
from geopandas import GeoDataFrame
from matplotlib.pyplot import figure
from shapely.geometry import Polygon

from prettymapp.geo import get_aoi
from prettymapp.osm import OsmDataError, get_osm_geometries
from prettymapp.plotting import Plot
from prettymapp.settings import STYLES

from data_kampus import (
    PRESET,
    PRESET_NAMES,
    UNIV_BY_NAMA,
    UNIVERSITAS,
    preset_untuk,
    slugify,
)

DIR_CONTOH = Path(__file__).parent / "example_prints"

# Terjemahan label untuk tampilan (nilai internal tetap sama dengan prettymapp).
LABEL_BENTUK = {"circle": "Lingkaran", "rectangle": "Persegi panjang", None: "Tanpa latar"}
LABEL_KELAS = {
    "urban": "Kawasan terbangun",
    "water": "Perairan",
    "grassland": "Padang rumput",
    "woodland": "Hutan / vegetasi",
    "streets": "Jalan",
    "other": "Lainnya",
}


# ---------------------------------------------------------------------------
# Fungsi bantu (dulunya utils.py pada versi asli)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False, hash_funcs={Polygon: lambda x: str(x.wkt)})
def st_get_osm_geometries(aoi):
    """Pembungkus agar unduhan data OSM di-cache oleh Streamlit."""
    return get_osm_geometries(aoi=aoi)


@st.cache_data(show_spinner=False)
def st_plot_all(_df: GeoDataFrame, **kwargs):
    """Pembungkus agar hasil gambar peta di-cache oleh Streamlit."""
    return Plot(_df, **kwargs).plot_all()


def get_colors_from_style(style: str) -> dict:
    """Mengembalikan dict {kelas_tutupan_lahan: warna}."""
    lc_class_colors = {}
    for lc_class, class_style in STYLES[style].items():
        colors = class_style.get("cmap", class_style.get("fc"))
        if isinstance(colors, list):
            for idx, color in enumerate(colors):
                lc_class_colors[f"{lc_class}_{idx}"] = color
        else:
            lc_class_colors[lc_class] = colors
    return lc_class_colors


def plt_to_svg(fig: figure) -> str:
    imgdata = StringIO()
    fig.savefig(
        imgdata, format="svg", pad_inches=0, bbox_inches="tight", transparent=True
    )
    imgdata.seek(0)
    return imgdata.getvalue()


def label_kelas(lc_class: str) -> str:
    """'urban_0' -> 'Kawasan terbangun (warna 1)'; 'water' -> 'Perairan'."""
    if "_" in lc_class:
        nama, idx = lc_class.split("_")
        return f"{LABEL_KELAS.get(nama, nama)} (warna {int(idx) + 1})"
    return LABEL_KELAS.get(lc_class, lc_class)


def pilih_kampus(nama: str) -> None:
    """Dipanggil saat tombol pada galeri diklik: pilih kampus + terapkan gayanya."""
    nama_preset = preset_untuk(nama)
    gaya = PRESET[nama_preset]["style"]
    warna = get_colors_from_style(gaya)
    st.session_state["univ"] = nama
    st.session_state.update(copy.deepcopy(PRESET[nama_preset]))
    st.session_state["radius"] = UNIV_BY_NAMA[nama]["radius"]
    st.session_state.update(warna)
    st.session_state.lc_classes = list(warna.keys())
    st.session_state["previous_style"] = gaya
    st.session_state["previous_preset"] = nama_preset


def ganti_kampus() -> None:
    """Dipanggil saat kampus diganti lewat dropdown: setel radius awal kampus itu."""
    st.session_state["radius"] = UNIV_BY_NAMA[st.session_state["univ"]]["radius"]


# ---------------------------------------------------------------------------
# Konfigurasi halaman
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Peta Kampus Cantik",
    page_icon="🗺️",
    initial_sidebar_state="collapsed",
)

st.markdown("# 🗺️ Visual Cantik Peta Kampus-kampus di Indonesia")
st.caption(
    "Buat peta artistik dari data OpenStreetMap di sekitar universitas-universitas "
    "di Indonesia. Pilih kampus, atur radius dan gaya, lalu unduh hasilnya."
)

# Inisialisasi status sesi (hanya sekali, saat aplikasi pertama kali dibuka).
if not st.session_state:
    st.session_state.update(copy.deepcopy(PRESET[PRESET_NAMES[0]]))
    lc_class_colors = get_colors_from_style("Peach")
    st.session_state.lc_classes = list(lc_class_colors.keys())
    st.session_state.update(lc_class_colors)
    st.session_state["previous_style"] = "Peach"
    st.session_state["previous_preset"] = PRESET_NAMES[0]
    st.session_state["univ"] = UNIVERSITAS[0]["nama"]
    st.session_state["radius"] = UNIVERSITAS[0]["radius"]


# ---------------------------------------------------------------------------
# Galeri contoh: klik untuk memilih kampus (gambar dibuat oleh generate_contoh.py)
# ---------------------------------------------------------------------------
st.markdown("##### Pilih kampus dari galeri")
KOLOM_GALERI = 5
for baris in range(0, len(UNIVERSITAS), KOLOM_GALERI):
    kolom = st.columns(KOLOM_GALERI)
    for kol, univ in zip(kolom, UNIVERSITAS[baris:baris + KOLOM_GALERI]):
        with kol:
            berkas = DIR_CONTOH / f"{slugify(univ['nama'])}.png"
            if berkas.exists():
                st.image(str(berkas))
            st.button(
                univ["singkatan"],
                key=f"galeri_{univ['singkatan']}",
                help=univ["nama"],
                on_click=pilih_kampus,
                args=(univ["nama"],),
                type="primary" if st.session_state.get("univ") == univ["nama"] else "secondary",
            )
if not DIR_CONTOH.exists() or not any(DIR_CONTOH.glob("*.png")):
    st.caption(
        "ℹ️ Gambar contoh belum tersedia. Jalankan `python generate_contoh.py` "
        "untuk membuatnya (lihat README). Aplikasi tetap berfungsi tanpa gambar."
    )

# ---------------------------------------------------------------------------
# Pilihan lokasi & preset
# ---------------------------------------------------------------------------
top1, top2 = st.columns([3, 2])
top1.selectbox(
    "Universitas terpilih",
    options=[u["nama"] for u in UNIVERSITAS],
    format_func=lambda n: f"{n} ({UNIV_BY_NAMA[n]['singkatan']})",
    key="univ",
    on_change=ganti_kampus,
)
preset_selected = top2.selectbox(
    "Preset gaya (opsional)",
    options=PRESET_NAMES,
    index=PRESET_NAMES.index(st.session_state["previous_preset"]),
    help="Menerapkan kombinasi gaya siap pakai. Setelah itu tiap pengaturan "
         "masih bisa diubah secara manual di bawah.",
)
if preset_selected != st.session_state["previous_preset"]:
    st.session_state.update(copy.deepcopy(PRESET[preset_selected]))
    st.session_state["radius"] = UNIV_BY_NAMA[st.session_state["univ"]]["radius"]
    st.session_state.update(get_colors_from_style(PRESET[preset_selected]["style"]))
    st.session_state["previous_style"] = PRESET[preset_selected]["style"]
    st.session_state["previous_preset"] = preset_selected

kampus = UNIV_BY_NAMA[st.session_state["univ"]]
st.caption(
    f"📍 **{kampus['nama']}** — lintang {kampus['lat']}, bujur {kampus['lon']} · "
    f"[lihat di OpenStreetMap]({kampus['osm']})"
)

# ---------------------------------------------------------------------------
# Formulir pengaturan
# ---------------------------------------------------------------------------
form = st.form(key="form_settings")
col1, col2 = form.columns([3, 2])
radius = col1.slider(
    "Radius (meter)",
    100,
    2000,
    key="radius",
    help="Semakin besar radius, semakin lama peta dibuat. Nilai awal disesuaikan "
         "dengan perkiraan luas tiap kampus; ubah bila area kampus kurang pas.",
)
style: str = col2.selectbox(
    "Tema warna",
    options=list(STYLES.keys()),
    key="style",
)

expander = form.expander("Kustomisasi gaya peta")
col1style, col2style, _, col3style = expander.columns([2, 2, 0.1, 1])

shape = col1style.radio(
    "Bentuk peta",
    options=["circle", "rectangle"],
    format_func=lambda v: LABEL_BENTUK[v],
    key="shape",
)
bg_shape = col1style.radio(
    "Bentuk latar belakang",
    options=["rectangle", "circle", None],
    format_func=lambda v: LABEL_BENTUK[v],
    key="bg_shape",
)
bg_color = col1style.color_picker("Warna latar belakang", key="bg_color")
bg_buffer = col1style.slider(
    "Ukuran latar belakang",
    min_value=0,
    max_value=50,
    help="Seberapa jauh latar belakang melebihi tepi peta.",
    key="bg_buffer",
)
col1style.markdown("---")
contour_color = col1style.color_picker("Warna kontur peta", key="contour_color")
contour_width = col1style.slider(
    "Ketebalan kontur peta",
    0,
    30,
    help="Ketebalan garis kontur yang mengelilingi peta.",
    key="contour_width",
)

name_on = col2style.checkbox(
    "Tampilkan judul",
    help="Jika dicentang, nama kampus ditampilkan sebagai judul peta. "
         "Dapat diganti pada kolom di bawahnya.",
    key="name_on",
)
custom_title = col2style.text_input(
    "Judul kustom (opsional)",
    max_chars=30,
    help="Kosongkan untuk memakai singkatan kampus (mis. UB, ITB, UGM).",
    key="custom_title",
)
font_size = col2style.slider("Ukuran huruf judul", min_value=1, max_value=50, key="font_size")
font_color = col2style.color_picker("Warna huruf judul", key="font_color")
text_x = col2style.slider("Judul kiri/kanan", -100, 100, key="text_x")
text_y = col2style.slider("Judul atas/bawah", -100, 100, key="text_y")
text_rotation = col2style.slider("Rotasi judul", -90, 90, key="text_rotation")

if style != st.session_state["previous_style"]:
    st.session_state.update(get_colors_from_style(style))

draw_settings = copy.deepcopy(STYLES[style])
for lc_class in st.session_state.lc_classes:
    picked_color = col3style.color_picker(label_kelas(lc_class), key=lc_class)
    if "_" in lc_class:
        kelas, idx = lc_class.split("_")
        draw_settings[kelas]["cmap"][int(idx)] = picked_color
    else:
        draw_settings[lc_class]["fc"] = picked_color

form.form_submit_button(label="Buat peta")

# ---------------------------------------------------------------------------
# Pembuatan peta
# ---------------------------------------------------------------------------
with st.spinner("Membuat peta… (dapat memakan waktu hingga satu menit)"):
    rectangular = shape != "circle"

    try:
        aoi = get_aoi(
            coordinates=(kampus["lat"], kampus["lon"]),
            radius=radius,
            rectangular=rectangular,
        )
    except ValueError as e:
        st.error(f"KESALAHAN: {e}")
        st.stop()

    try:
        df = st_get_osm_geometries(aoi=aoi)
    except OsmDataError:
        st.error(
            "KESALAHAN: Tidak ditemukan data OpenStreetMap yang dapat digunakan "
            "pada area ini. Coba perbesar radius."
        )
        st.stop()
    except Exception:  # pylint: disable=broad-except
        st.error(
            "KESALAHAN: Data OpenStreetMap untuk area ini tidak dapat diunduh. "
            "Layanan mungkin sedang sibuk atau tidak tersedia — silakan coba "
            "lagi, atau kecilkan radius."
        )
        st.stop()

    judul = kampus["singkatan"] if custom_title == "" else custom_title
    config = {
        "aoi_bounds": aoi.bounds,
        "draw_settings": draw_settings,
        "name_on": name_on,
        "name": judul,
        "font_size": font_size,
        "font_color": font_color,
        "text_x": text_x,
        "text_y": text_y,
        "text_rotation": text_rotation,
        "shape": shape,
        "contour_width": contour_width,
        "contour_color": contour_color,
        "bg_shape": bg_shape,
        "bg_buffer": bg_buffer,
        "bg_color": bg_color,
    }

    try:
        fig = st_plot_all(_df=df, **config)
    except Exception:  # pylint: disable=broad-except
        st.error("KESALAHAN: Peta untuk area ini tidak dapat digambar. Silakan coba lagi.")
        st.stop()

_buf_tampil = io.BytesIO()
fig.savefig(_buf_tampil, format="png", dpi=200, pad_inches=0, bbox_inches="tight", transparent=True)
st.image(_buf_tampil.getvalue())
st.markdown("</br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Ekspor
# ---------------------------------------------------------------------------
fname_base = slugify(kampus["nama"]) or "peta-kampus"

with st.expander("Ekspor gambar"):
    img_format = st.selectbox(
        "Jenis berkas",
        options=["png", "svg"],
        index=0,
        help="Ekspor peta dalam format berbeda.",
        key="export_image_format",
        format_func=lambda v: "PNG (300 dpi)" if v == "png" else "SVG (tanpa kehilangan kualitas)",
    )
    mime_by_format = {"png": "image/png", "svg": "image/svg+xml"}

    def _make_download_data():
        # Dijalankan hanya saat tombol diklik.
        if img_format == "svg":
            return plt_to_svg(fig)
        buf = io.BytesIO()
        savefig_kwargs = dict(
            format=img_format, pad_inches=0, bbox_inches="tight", transparent=True
        )
        if img_format == "png":
            savefig_kwargs["dpi"] = 300
        fig.savefig(buf, **savefig_kwargs)
        buf.seek(0)
        return buf.getvalue()

    st.download_button(
        label="Unduh",
        data=_make_download_data,
        file_name=f"{fname_base}.{img_format}",
        mime=mime_by_format[img_format],
        on_click="ignore",
        key=f"download_image_{img_format}",
    )

ex1, ex2 = st.columns(2)
with ex1.expander("Ekspor geometri sebagai GeoJSON"):
    st.write(f"{df.shape[0]} geometri")
    st.download_button(
        label="Unduh",
        data=lambda: df.to_json().encode("utf-8"),
        file_name=f"{fname_base}.geojson",
        mime="application/geo+json",
        on_click="ignore",
    )

with ex2.expander("Ekspor konfigurasi peta"):
    st.write(
        {
            "kampus": kampus["nama"],
            "lintang": kampus["lat"],
            "bujur": kampus["lon"],
            "tautan_osm": kampus["osm"],
            **config,
        }
    )

with st.expander("Daftar universitas & koordinat"):
    st.dataframe(
        [
            {
                "Universitas": u["nama"],
                "Singkatan": u["singkatan"],
                "Lintang": u["lat"],
                "Bujur": u["lon"],
                "Radius awal (m)": u["radius"],
                "OSM": u["osm"],
            }
            for u in UNIVERSITAS
        ],
        hide_index=True,
        column_config={"OSM": st.column_config.LinkColumn("OSM", display_text="Buka peta")},
    )

st.markdown("---")
st.markdown(
    "Data peta © kontributor [OpenStreetMap](https://www.openstreetmap.org/copyright). "
    "Dibangun oleh Adipandang Yudono (2026)." 
)

st.session_state["previous_style"] = style
