"""Pembuatan dataset teks sintetis yang deterministik."""

from __future__ import annotations

import random
import string
from pathlib import Path

NAMA = "Adithya Nurrahman"
NIM = "247006111176"

DEFAULT_THREADS = int(NIM[-2:]) % 4 + 2
DEFAULT_PROCESSES = int(NIM[5:7]) % 3 + 2
DEFAULT_DATA = int(NIM[-3:]) * 10

DATASET_DIR = Path(__file__).resolve().parent / "dataset"
MIN_FILE_SIZE = 20 * 1024
MAX_FILE_SIZE = 50 * 1024

_WORDS = (
    "parallel computing simulation distributed processor memory data analysis "
    "thread process hybrid system algorithm measurement performance result "
    "model sensor network temperature velocity acceleration function"
).split()
_SYMBOLS = string.punctuation


def ensure_dataset(data: int, dataset_dir: Path = DATASET_DIR) -> list[Path]:
    """Buat tepat sejumlah file dataset; lewati bila jumlahnya sudah sesuai."""
    if data < 0:
        raise ValueError("Jumlah data tidak boleh negatif.")

    # Simpan tiap ukuran terpisah agar eksperimen dapat menyiapkannya sekaligus.
    target_dir = (
        dataset_dir / f"data_{data}"
        if dataset_dir == DATASET_DIR
        else dataset_dir
    )
    target_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(target_dir.glob("*.txt"))
    if len(existing) == data:
        return existing

    for path in existing:
        path.unlink()

    # Seed diulang agar isi dataset sama setiap kali perlu dibuat ulang.
    random.seed(int(NIM))
    paths: list[Path] = []
    for file_index in range(data):
        path = target_dir / f"data_{file_index + 1:05d}.txt"
        target_size = random.randint(MIN_FILE_SIZE, MAX_FILE_SIZE)
        remaining = target_size
        with path.open("w", encoding="ascii", newline="") as output:
            while remaining:
                token_type = random.randrange(4)
                if token_type == 0:
                    token = random.choice(_WORDS)
                elif token_type == 1:
                    token = str(random.randrange(10**3, 10**10))
                elif token_type == 2:
                    token = random.choice(_SYMBOLS)
                else:
                    token = " "
                fragment = token[:remaining]
                output.write(fragment)
                remaining -= len(fragment)
        paths.append(path)
    return paths