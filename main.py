"""Menjalankan benchmark Parallel File Analyzer."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from itertools import islice
import multiprocessing
import os
import time
from typing import Iterable, Iterator

from analyzer import analyze_batch, analyze_text, merge_totals
from data_generator import (
    DEFAULT_DATA,
    DEFAULT_PROCESSES,
    DEFAULT_THREADS,
    NAMA,
    NIM,
    ensure_dataset,
)

BATCH_SIZE = 24


def get_machine_info() -> dict[str, int | None]:
    """Ambil jumlah CPU logis dan jumlah CPU fisik bila psutil tersedia."""
    logical = os.cpu_count() or 1
    try:
        import psutil

        physical = psutil.cpu_count(logical=False)
    except ImportError:
        physical = None
    return {"logical": logical, "physical": physical}


def _empty_totals() -> dict[str, object]:
    from collections import Counter

    return {
        "vowels": 0,
        "words": 0,
        "numbers": 0,
        "symbols": 0,
        "word_frequency": Counter(),
    }


def _batches(items: Iterable, batch_size: int) -> Iterator[list]:
    iterator = iter(items)
    while batch := list(islice(iterator, batch_size)):
        yield batch


def _read_batch(paths: list) -> list[str]:
    """Baca batch file di thread pool; hanya teks dikirim ke process pool."""
    return [path.read_text(encoding="ascii") for path in paths]


def _measure_sequential(paths: list) -> float:
    sequential_totals = _empty_totals()
    start = time.perf_counter()
    for path in paths:
        result = analyze_text(path.read_text(encoding="ascii"))
        merge_totals(sequential_totals, result)
    return time.perf_counter() - start


def run_sequential(data: int) -> float:
    """Ukur satu kali baseline sekuensial tanpa menghitung waktu generator."""
    return _measure_sequential(ensure_dataset(data))


def run_hybrid(
    threads: int,
    processes: int,
    data: int,
    include_sequential: bool = True,
) -> dict[str, object]:
    """Jalankan baseline dan pipeline hybrid, lalu kembalikan metrik lengkap."""
    if threads < 1 or processes < 1:
        raise ValueError("Threads dan processes harus minimal 1.")
    paths = ensure_dataset(data)

    sequential_time = _measure_sequential(paths) if include_sequential else None

    hybrid_totals = _empty_totals()
    start = time.perf_counter()
    # MPI tidak digunakan karena seluruh worker berjalan pada satu mesin.
    with ThreadPoolExecutor(max_workers=threads) as reader_pool:
        with ProcessPoolExecutor(max_workers=processes) as analyzer_pool:
            read_futures = [
                reader_pool.submit(_read_batch, batch)
                for batch in _batches(paths, BATCH_SIZE)
            ]
            # Setiap batch yang selesai dibaca langsung masuk antrean CPU.
            analysis_futures = []
            for read_future in as_completed(read_futures):
                texts = read_future.result()
                analysis_futures.append(analyzer_pool.submit(analyze_batch, texts))
            for analysis_future in as_completed(analysis_futures):
                merge_totals(hybrid_totals, analysis_future.result())
    parallel_time = time.perf_counter() - start

    speedup = (
        sequential_time / parallel_time
        if sequential_time is not None and parallel_time > 0
        else None
    )
    efficiency = speedup / processes * 100 if speedup is not None else None
    throughput = data / parallel_time if parallel_time > 0 else 0.0
    return {
        "threads": threads,
        "processes": processes,
        "data": data,
        "sequential_time": sequential_time,
        "parallel_time": parallel_time,
        "speedup": speedup,
        "efficiency": efficiency,
        "throughput": throughput,
        "totals": hybrid_totals,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Parallel File Analyzer")
    parser.add_argument("--threads", type=int, default=DEFAULT_THREADS)
    parser.add_argument("--processes", type=int, default=DEFAULT_PROCESSES)
    parser.add_argument("--data", type=int, default=DEFAULT_DATA)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    machine = get_machine_info()
    results = run_hybrid(args.threads, args.processes, args.data)
    totals = results["totals"]
    assert isinstance(totals, dict)

    print(f"Hybrid Project by: {NAMA} ({NIM})")
    print(
        f"Threads: {args.threads} | Processes: {args.processes} | "
        f"Data: {args.data}"
    )
    print(
        f"Total Time: {results['parallel_time']:.4f} s | "
        f"Speedup: {results['speedup']:.4f} | "
        f"Efficiency: {results['efficiency']:.2f}%"
    )
    print(f"Throughput: {results['throughput']:.2f} file/detik")
    physical_text = (
        str(machine["physical"])
        if machine["physical"] is not None
        else "tidak tersedia (psutil belum terpasang)"
    )
    print(
        f"Info CPU: logical={machine['logical']} | physical={physical_text}"
    )
    print(
        "Hasil analisis: "
        f"total vokal={totals['vowels']} | kata={totals['words']} | "
        f"angka={totals['numbers']} | simbol={totals['symbols']} | "
        f"jumlah file={args.data}"
    )


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()