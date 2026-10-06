"""Analisis teks dan fungsi reduksi untuk hasil worker."""

from __future__ import annotations

from collections import Counter
import re

_WORD_PATTERN = re.compile(r"[A-Za-z]+")
_VOWELS = frozenset("aeiouAEIOU")


def analyze_text(text: str) -> dict[str, object]:
    """Hitung vokal, kata, angka, simbol, dan frekuensi kata pada teks."""
    words = _WORD_PATTERN.findall(text)
    return {
        "vowels": sum(character in _VOWELS for character in text),
        "words": len(words),
        "numbers": sum(character.isdigit() for character in text),
        "symbols": sum(
            not character.isalnum() and not character.isspace()
            for character in text
        ),
        "word_frequency": Counter(word.lower() for word in words),
    }


def analyze_batch(texts: list[str]) -> dict[str, object]:
    """Analisis satu batch di process worker agar overhead pickle terkendali."""
    totals: dict[str, object] = {
        "vowels": 0,
        "words": 0,
        "numbers": 0,
        "symbols": 0,
        "word_frequency": Counter(),
    }
    frequencies = totals["word_frequency"]
    assert isinstance(frequencies, Counter)
    for text in texts:
        result = analyze_text(text)
        for key in ("vowels", "words", "numbers", "symbols"):
            totals[key] = int(totals[key]) + int(result[key])
        frequencies.update(result["word_frequency"])
    return totals


def merge_totals(total: dict[str, object], partial: dict[str, object]) -> None:
    """Gabungkan hasil satu worker ke accumulator utama."""
    for key in ("vowels", "words", "numbers", "symbols"):
        total[key] = int(total[key]) + int(partial[key])
    total_frequency = total["word_frequency"]
    partial_frequency = partial["word_frequency"]
    assert isinstance(total_frequency, Counter)
    assert isinstance(partial_frequency, Counter)
    total_frequency.update(partial_frequency)