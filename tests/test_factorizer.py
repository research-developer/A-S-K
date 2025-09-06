from __future__ import annotations

from ask.factorizer import extract_consonant_clusters, extract_vowel_sequence, decode_word


def test_extract_consonant_clusters_basic():
    assert extract_consonant_clusters("ask") == ["sk"] or extract_consonant_clusters("ask") == ["a", "s", "k"]


def test_extract_vowel_sequence_basic():
    assert extract_vowel_sequence("manipulation") == [c for c in "manipulation" if c in "aeiouy"]


def test_decode_word_program_nonempty():
    d = decode_word("manipulation")
    assert d["program"], "program should not be empty"
