# Parallel File Analyzer

Proyek UTS Komputasi Paralel dan Terdistribusi dengan tema **Hybrid Computing for Real-World Simulation and Data Processing**. Parallel File Analyzer membuat kumpulan file teks sintetis, menganalisis isi file, lalu membandingkan waktu eksekusi sekuensial dengan pemrosesan hybrid.

Analisis menghitung vokal, kata, digit, simbol, dan frekuensi kata. Thread menangani pembacaan file yang bersifat I/O-bound, sedangkan process worker menangani analisis batch yang bersifat CPU-bound. Hasil batch direduksi menjadi statistik total. MPI tidak digunakan karena seluruh worker berjalan pada satu mesin.

## Arsitektur

```mermaid
flowchart LR
	A[Dataset] --> B[Thread Pool<br/>I/O: membaca file]
	B --> C[Chunk Queue<br/>batch teks]
	C --> D[Process Pool<br/>CPU: analisis teks]
	D --> E[Reduce<br/>gabung statistik]
	E --> F[Output<br/>metrik, CSV, grafik]
```

Selain jalur hybrid, `main.py` menghitung baseline sekuensial untuk memperoleh speedup dan efisiensi. Pada `experiment.py`, ukuran dataset disiapkan sebelum timer benchmark berjalan.

## Instalasi

Gunakan Python 3.10 atau lebih baru. Buat virtual environment dan pasang dependensi proyek:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Jika PowerShell memblokir aktivasi script pada sesi ini, izinkan aktivasi hanya untuk proses terminal saat ini dengan `Set-ExecutionPolicy -Scope Process Bypass`, lalu aktifkan kembali virtual environment. `psutil` dipakai untuk informasi CPU fisik/RAM jika tersedia; `matplotlib` untuk grafik; `pandas` tersedia untuk analisis CSV lanjutan. Generator, analyzer, dan benchmark inti menggunakan standard library.

## Menjalankan

Jalankan benchmark utama. Argumen opsional dapat menimpa parameter default:

```powershell
python main.py
python main.py --threads 4 --processes 2 --data 100
```

Jalankan eksperimen 10 konfigurasi. Script melakukan satu warm-up yang tidak dicatat, mengulang setiap konfigurasi tiga kali, dan menyimpan rata-rata serta metrik ke `results.csv`. Informasi mesin ditulis ke `machine_info.txt`.

```powershell
python experiment.py
```

Buat tiga grafik PNG dari `results.csv`; hasil disimpan ke folder `hasil/`.

```powershell
python plot_results.py
```

Generator menyimpan file ASCII sintetis berukuran 20-50 KB di `dataset/data_<jumlah>/`. Isi dibuat deterministik menggunakan seed NIM. Cache ukuran yang berbeda tetap dipertahankan.

## Parameter NIM

Parameter default dihitung dari NIM `247006111176` pada `data_generator.py`:

| Parameter | Rumus | Perhitungan | Hasil |
| --- | --- | --- | ---: |
| Threads | `int(NIM[-2:]) % 4 + 2` | `76 % 4 + 2` | 2 |
| Processes | `int(NIM[5:7]) % 3 + 2` | `61 % 3 + 2` | 3 |
| Data | `int(NIM[-3:]) * 10` | `176 * 10` | 1.760 file |

Nama yang dicetak program: **Adithya Nurrahman**. Nilai parameter dapat ditimpa lewat opsi `--threads`, `--processes`, dan `--data`.

## Definisi metrik

- Throughput = jumlah file / waktu hybrid (file/detik).
- Speedup = waktu sekuensial / waktu hybrid.
- Efisiensi = speedup / jumlah process * 100%.
- Simbol adalah karakter non-alfanumerik selain whitespace; kata adalah rangkaian huruf ASCII.

## Spesifikasi Mesin

Berikut informasi yang tercatat di `machine_info.txt` saat eksperimen dijalankan:

| Komponen | Spesifikasi |
| --- | --- |
| CPU | AMD64 Family 25 Model 124 Stepping 0, AuthenticAMD |
| Core logical | 12 |
| Core physical | 6 |
| RAM | 15.23 GB |
| Sistem operasi | Windows-11-10.0.26200-SP0 |
| Versi Python | 3.14.7 |

Spesifikasi ini berasal dari mesin yang menjalankan eksperimen dan dapat berbeda pada mesin lain. Jalankan ulang `python experiment.py` untuk memperbarui `machine_info.txt`.