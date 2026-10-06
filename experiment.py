"""Benchmark sepuluh konfigurasi Parallel File Analyzer."""

from __future__ import annotations

import csv
import os
import platform
from pathlib import Path
import statistics
import sys
from typing import Any

from data_generator import (
    DATASET_DIR,
    DEFAULT_DATA,
    DEFAULT_PROCESSES,
    DEFAULT_THREADS,
    ensure_dataset,
)
from main import get_machine_info, run_hybrid, run_sequential


REPETITIONS = 3
OUTPUT_DIR = Path(__file__).resolve().parent


def _process_variations(logical_cores: int) -> list[int]:
    """Pilih tiga nilai proses yang terurut dan tetap mencakup jumlah CPU."""
    logical_cores = max(1, logical_cores)
    candidates = {1, 2, 4, logical_cores} - {3}
    while len(candidates) < 3:
        candidates.add(2 * logical_cores)

    if len(candidates) > 3:
        selected = {1, 4, logical_cores}
    else:
        selected = candidates
    return sorted(selected)


def _build_configurations(logical_cores: int) -> list[dict[str, int]]:
    configurations = [
        {
            "No": 1,
            "Threads": DEFAULT_THREADS,
            "Processes": DEFAULT_PROCESSES,
            "Data": DEFAULT_DATA,
        }
    ]
    for number, threads in enumerate((1, 4, 8), start=2):
        configurations.append(
            {
                "No": number,
                "Threads": threads,
                "Processes": DEFAULT_PROCESSES,
                "Data": DEFAULT_DATA,
            }
        )
    for number, processes in enumerate(_process_variations(logical_cores), start=5):
        configurations.append(
            {
                "No": number,
                "Threads": DEFAULT_THREADS,
                "Processes": processes,
                "Data": DEFAULT_DATA,
            }
        )
    for number, data in enumerate((880, 3520, 7040), start=8):
        configurations.append(
            {
                "No": number,
                "Threads": DEFAULT_THREADS,
                "Processes": DEFAULT_PROCESSES,
                "Data": data,
            }
        )
    return configurations


def _ram_total_bytes() -> int | None:
    try:
        import psutil

        return int(psutil.virtual_memory().total)
    except ImportError:
        if os.name == "nt":
            import ctypes

            class MemoryStatus(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            status = MemoryStatus()
            status.dwLength = ctypes.sizeof(status)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return int(status.ullTotalPhys)
        elif hasattr(os, "sysconf"):
            return int(os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES"))
    return None


def _write_machine_info(machine: dict[str, int | None]) -> None:
    cpu_name = (
        platform.processor()
        or os.environ.get("PROCESSOR_IDENTIFIER")
        or platform.machine()
    )
    physical = machine["physical"]
    ram = _ram_total_bytes()
    ram_text = f"{ram / (1024 ** 3):.2f} GB" if ram is not None else "Tidak tersedia"
    physical_text = str(physical) if physical is not None else "Tidak tersedia"
    contents = (
        f"Nama CPU: {cpu_name}\n"
        f"Core logical: {machine['logical']}\n"
        f"Core physical: {physical_text}\n"
        f"RAM: {ram_text}\n"
        f"OS: {platform.platform()}\n"
        f"Versi Python: {sys.version.split()[0]}\n"
    )
    (OUTPUT_DIR / "machine_info.txt").write_text(contents, encoding="utf-8")


def _format_table(rows: list[dict[str, Any]], headers: list[str]) -> str:
    values = [[str(row[header]) for header in headers] for row in rows]
    widths = [
        max(len(header), *(len(row[index]) for row in values))
        for index, header in enumerate(headers)
    ]
    header_line = " | ".join(
        header.ljust(widths[index]) for index, header in enumerate(headers)
    )
    separator = "-+-".join("-" * width for width in widths)
    body = [
        " | ".join(value.rjust(widths[index]) for index, value in enumerate(row))
        for row in values
    ]
    return "\n".join([header_line, separator, *body])


def main() -> None:
    machine = get_machine_info()
    configurations = _build_configurations(machine["logical"] or 1)
    dataset_sizes = sorted({row["Data"] for row in configurations}, reverse=True)

    # Persiapkan semua ukuran sebelum timer benchmark dimulai.
    for data_size in dataset_sizes:
        ensure_dataset(data_size, DATASET_DIR)

    # Satu warm-up tidak masuk ke hasil maupun rata-rata.
    first = configurations[0]
    run_hybrid(
        first["Threads"],
        first["Processes"],
        first["Data"],
        include_sequential=False,
    )

    sequential_averages = {
        data_size: statistics.mean(
            run_sequential(data_size) for _ in range(REPETITIONS)
        )
        for data_size in sorted({row["Data"] for row in configurations})
    }

    results: list[dict[str, Any]] = []
    for configuration in configurations:
        parallel_samples = [
            run_hybrid(
                configuration["Threads"],
                configuration["Processes"],
                configuration["Data"],
                include_sequential=False,
            )["parallel_time"]
            for _ in range(REPETITIONS)
        ]
        parallel_average = statistics.mean(parallel_samples)
        sequential_average = sequential_averages[configuration["Data"]]
        speedup = sequential_average / parallel_average
        results.append(
            {
                **configuration,
                "Waktu_s": parallel_average,
                "Speedup": speedup,
                "Efisiensi_persen": speedup / configuration["Processes"] * 100,
                "Waktu_Seq_s": sequential_average,
                "Throughput": configuration["Data"] / parallel_average,
            }
        )

    columns = [
        "No", "Threads", "Processes", "Data", "Waktu_s", "Speedup",
        "Efisiensi_persen", "Waktu_Seq_s", "Throughput",
    ]
    csv_path = OUTPUT_DIR / "results.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(results)

    _write_machine_info(machine)
    display_rows = [
        {
            **row,
            "Waktu_s": f"{row['Waktu_s']:.4f}",
            "Speedup": f"{row['Speedup']:.4f}",
            "Efisiensi_persen": f"{row['Efisiensi_persen']:.2f}",
            "Waktu_Seq_s": f"{row['Waktu_Seq_s']:.4f}",
            "Throughput": f"{row['Throughput']:.2f}",
        }
        for row in results
    ]
    print(_format_table(display_rows, columns))
    print(f"\nHasil tersimpan: {csv_path}")
    print(f"Informasi mesin tersimpan: {OUTPUT_DIR / 'machine_info.txt'}")


if __name__ == "__main__":
    main()