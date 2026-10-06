"""Buat grafik hasil eksperimen Parallel File Analyzer."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REQUIRED_COLUMNS = {"No", "Threads", "Processes", "Waktu_s", "Speedup"}


def _annotate_points(axis, x_values: list[int], y_values: list[float]) -> None:
    for x_value, y_value in zip(x_values, y_values):
        axis.annotate(
            f"{y_value:.2f}",
            (x_value, y_value),
            textcoords="offset points",
            xytext=(0, 7),
            ha="center",
            fontsize=9,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Grafik hasil eksperimen paralel")
    parser.add_argument(
        "csv_file",
        nargs="?",
        type=Path,
        default=BASE_DIR / "results.csv",
        help="Lokasi results.csv (default: di folder proyek)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=BASE_DIR / "hasil",
        help="Folder penyimpanan grafik (default: ./hasil)",
    )
    args = parser.parse_args()

    try:
        import matplotlib.pyplot as plt
    except ImportError as error:
        raise SystemExit("Pasang matplotlib dengan: pip install matplotlib") from error

    with args.csv_file.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        missing_columns = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise SystemExit(f"Kolom CSV tidak lengkap: {missing}")
        rows = [
            {
                "No": int(row["No"]),
                "Threads": int(row["Threads"]),
                "Processes": int(row["Processes"]),
                "Waktu_s": float(row["Waktu_s"]),
                "Speedup": float(row["Speedup"]),
            }
            for row in reader
        ]
    if not rows:
        raise SystemExit("File CSV tidak berisi hasil eksperimen.")

    by_number = {row["No"]: row for row in rows}
    required_numbers = set(range(1, 11))
    if not required_numbers.issubset(by_number):
        raise SystemExit("CSV harus memuat konfigurasi No 1 sampai No 10.")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    thread_rows = sorted(
        (by_number[number] for number in range(1, 5)),
        key=lambda row: row["Threads"],
    )
    thread_values = [row["Threads"] for row in thread_rows]
    thread_times = [row["Waktu_s"] for row in thread_rows]
    figure, axis = plt.subplots(figsize=(8, 5))
    axis.plot(thread_values, thread_times, marker="o", linewidth=2, color="#087e8b")
    _annotate_points(axis, thread_values, thread_times)
    axis.set(
        title="Waktu Eksekusi terhadap Jumlah Thread",
        xlabel="Jumlah Thread",
        ylabel="Waktu Rata-rata (detik)",
    )
    axis.set_xticks(thread_values)
    axis.grid(True, linestyle="--", alpha=0.45)
    figure.tight_layout()
    figure.savefig(args.output_dir / "waktu_vs_thread.png", dpi=150)
    plt.close(figure)

    process_rows = sorted(
        [by_number[1], *(by_number[number] for number in range(5, 8))],
        key=lambda row: row["Processes"],
    )
    process_values = [row["Processes"] for row in process_rows]
    process_times = [row["Waktu_s"] for row in process_rows]
    figure, axis = plt.subplots(figsize=(8, 5))
    axis.plot(process_values, process_times, marker="o", linewidth=2, color="#e76f51")
    _annotate_points(axis, process_values, process_times)
    axis.set(
        title="Waktu Eksekusi terhadap Jumlah Process",
        xlabel="Jumlah Process",
        ylabel="Waktu Rata-rata (detik)",
    )
    axis.set_xticks(process_values)
    axis.grid(True, linestyle="--", alpha=0.45)
    figure.tight_layout()
    figure.savefig(args.output_dir / "waktu_vs_process.png", dpi=150)
    plt.close(figure)

    all_rows = sorted(rows, key=lambda row: row["No"])
    configuration_numbers = [row["No"] for row in all_rows]
    speedups = [row["Speedup"] for row in all_rows]
    figure, axis = plt.subplots(figsize=(10, 5))
    bars = axis.bar(configuration_numbers, speedups, color="#4c956c", width=0.72)
    for bar, value in zip(bars, speedups):
        axis.annotate(
            f"{value:.2f}",
            (bar.get_x() + bar.get_width() / 2, bar.get_height()),
            textcoords="offset points",
            xytext=(0, 4),
            ha="center",
            va="bottom",
            fontsize=9,
        )
    axis.set(
        title="Speedup pada Setiap Konfigurasi",
        xlabel="Nomor Konfigurasi",
        ylabel="Speedup (kali)",
    )
    axis.set_xticks(configuration_numbers)
    axis.grid(True, axis="y", linestyle="--", alpha=0.45)
    axis.set_axisbelow(True)
    figure.tight_layout()
    figure.savefig(args.output_dir / "speedup_vs_konfigurasi.png", dpi=150)
    plt.close(figure)

    print(f"Tiga grafik berhasil disimpan di: {args.output_dir}")


if __name__ == "__main__":
    main()
