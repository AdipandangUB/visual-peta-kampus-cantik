"""
Membuat gambar contoh (thumbnail) tiap kampus untuk galeri di app.py.

Cara pakai (butuh koneksi internet, jalankan di komputer sendiri):
    pip install prettymapp pyogrio
    python generate_contoh.py            # semua kampus (~10-20 menit)
    python generate_contoh.py UB ITB     # hanya kampus tertentu (singkatan)
    python generate_contoh.py --ulang    # timpa gambar yang sudah ada

Hasil: example_prints/<nama-universitas>.png
Kampus yang sudah punya gambar dilewati, jadi skrip aman dijalankan ulang
bila sebagian gagal (mis. server Overpass sedang sibuk).
"""

import copy
import sys
import time
from pathlib import Path

import prettymapp.osm as osm
from prettymapp.geo import get_aoi
from prettymapp.plotting import Plot
from prettymapp.settings import STYLES

from data_kampus import PRESET, UNIVERSITAS, preset_untuk, slugify

FOLDER = Path(__file__).parent / "example_prints"
JEDA_DETIK = 5  # jeda antar kampus agar tidak membebani server Overpass


def buat_gambar(univ: dict) -> Path:
    cfg = PRESET[preset_untuk(univ["nama"])]
    aoi = get_aoi(
        coordinates=(univ["lat"], univ["lon"]),
        radius=univ["radius"],
        rectangular=cfg["shape"] != "circle",
    )
    df = osm.get_osm_geometries(aoi=aoi)
    fig = Plot(
        df,
        aoi_bounds=aoi.bounds,
        draw_settings=copy.deepcopy(STYLES[cfg["style"]]),
        name_on=cfg["name_on"],
        name=univ["singkatan"],
        font_size=cfg["font_size"],
        font_color=cfg["font_color"],
        text_x=cfg["text_x"],
        text_y=cfg["text_y"],
        text_rotation=cfg["text_rotation"],
        shape=cfg["shape"],
        contour_width=cfg["contour_width"],
        contour_color=cfg["contour_color"],
        bg_shape=cfg["bg_shape"],
        bg_buffer=cfg["bg_buffer"],
        bg_color=cfg["bg_color"],
    ).plot_all()
    FOLDER.mkdir(exist_ok=True)
    tujuan = FOLDER / f"{slugify(univ['nama'])}.png"
    fig.savefig(tujuan, dpi=45, bbox_inches="tight", pad_inches=0, transparent=True)
    return tujuan


def main(argumen: list) -> None:
    ulang = "--ulang" in argumen
    pilihan = {a.lower() for a in argumen if not a.startswith("--")}
    daftar = [u for u in UNIVERSITAS if not pilihan or u["singkatan"].lower() in pilihan]
    if not daftar:
        sys.exit("Singkatan tidak dikenali. Contoh: UB UI ITB UGM IPB Unpad ...")

    gagal = []
    for n, univ in enumerate(daftar, 1):
        tujuan = FOLDER / f"{slugify(univ['nama'])}.png"
        if tujuan.exists() and not ulang:
            print(f"[{n}/{len(daftar)}] {univ['singkatan']}: sudah ada, dilewati")
            continue
        print(f"[{n}/{len(daftar)}] {univ['singkatan']}: mengunduh data OSM…", flush=True)
        try:
            print("   ->", buat_gambar(univ).name)
        except Exception as e:  # noqa: BLE001
            print(f"   GAGAL: {e}")
            gagal.append(univ["singkatan"])
        time.sleep(JEDA_DETIK)

    print("\nSelesai." + (f" Gagal: {', '.join(gagal)} — jalankan ulang untuk mencoba lagi." if gagal else ""))


if __name__ == "__main__":
    main(sys.argv[1:])
