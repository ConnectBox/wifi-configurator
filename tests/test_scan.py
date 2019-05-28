#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wifi_configurator import scan

def test_get_country_count_populated(iw_dev_scan_0):
    c = scan.get_country_count_from_iw_output(iw_dev_scan_0)
    assert c.most_common(1)[0][0] == "TR"
    assert len(list(c.elements())) == 4
    assert c["AL"] == 1

def test_get_country_count_unpopulated(iw_dev_scan_1):
    c = scan.get_country_count_from_iw_output(iw_dev_scan_1)
    assert c.most_common(1) == []
    assert not list(c.elements())

def test_get_country_count_empty(iw_dev_scan_2):
    c = scan.get_country_count_from_iw_output(iw_dev_scan_2)
    assert c.most_common(1) == []
    assert not list(c.elements())

def test_get_country_count_populated2(iw_dev_scan_3):
    c = scan.get_country_count_from_iw_output(iw_dev_scan_3)
    assert c.most_common(1)[0][0] == "AU"
    assert len(list(c.elements())) == 2

AU_REGDB = """\
country AU: DFS-ETSI
	(2402.000 - 2482.000 @ 40.000), (20.00), (N/A)
	(5170.000 - 5250.000 @ 80.000), (17.00), (N/A), AUTO-BW
	(5250.000 - 5330.000 @ 80.000), (24.00), (N/A), DFS, AUTO-BW
	(5490.000 - 5710.000 @ 160.000), (24.00), (N/A), DFS
	(5735.000 - 5835.000 @ 80.000), (30.00), (N/A)"""
def test_get_country_rules_block_matching(regdb_lines):
    block_lines = scan.get_country_rules_block("AU", regdb_lines)
    assert block_lines == AU_REGDB.split("\n")

def test_au_freq_extraction(regdb_lines):
    block_lines = scan.get_country_rules_block("AU", regdb_lines)
    freq_blocks = scan.get_frequencies_from_country_block(block_lines)
    assert freq_blocks == [
        (2402, 2482),
        (5170, 5250),
        (5250, 5330),
        (5490, 5710),
        (5735, 5835),
    ]

def test_flattening_of_au_freqs(regdb_lines):
    block_lines = scan.get_country_rules_block("AU", regdb_lines)
    freq_blocks = scan.get_frequencies_from_country_block(block_lines)
    freq_blocks = scan.flatten_frequency_blocks(freq_blocks)
    assert scan.flatten_frequency_blocks(freq_blocks) == [
        (2402, 2482),
        (5170, 5330),
        (5490, 5710),
        (5735, 5835),
    ]

def test_channel_list_au(regdb_lines):
    block_lines = scan.get_country_rules_block("AU", regdb_lines)
    freq_blocks = scan.get_frequencies_from_country_block(block_lines)
    freq_blocks = scan.flatten_frequency_blocks(freq_blocks)
    assert scan.get_channel_list_from_frequency_blocks(freq_blocks) == \
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]


UNSET_REGDB = """\
country 00: DFS-UNSET
	(2402.000 - 2472.000 @ 40.000), (20.00), (N/A)
	(2457.000 - 2482.000 @ 20.000), (20.00), (N/A), NO-IR, AUTO-BW
	(2474.000 - 2494.000 @ 20.000), (20.00), (N/A), NO-OFDM, NO-IR
	(5170.000 - 5250.000 @ 80.000), (20.00), (N/A), NO-IR, AUTO-BW
	(5250.000 - 5330.000 @ 80.000), (20.00), (N/A), DFS, NO-IR, AUTO-BW
	(5490.000 - 5730.000 @ 160.000), (20.00), (N/A), DFS, NO-IR
	(5735.000 - 5835.000 @ 80.000), (20.00), (N/A), NO-IR
	(57240.000 - 63720.000 @ 2160.000), (N/A), (N/A)"""

def test_get_country_rules_block_first(regdb_lines):
    block_lines = scan.get_country_rules_block("00", regdb_lines)
    assert block_lines == UNSET_REGDB.split("\n")

def test_unset_freq_extraction(regdb_lines):
    block_lines = scan.get_country_rules_block("00", regdb_lines)
    freq_blocks = scan.get_frequencies_from_country_block(block_lines)
    assert freq_blocks == [
        (2402, 2472),
        (2457, 2474),
        (5170, 5250),
        (5250, 5330),
        (5490, 5730),
        (5735, 5835),
        (57240, 63720),
    ]

def test_flattening_of_unset_freqs(regdb_lines):
    block_lines = scan.get_country_rules_block("00", regdb_lines)
    freq_blocks = scan.get_frequencies_from_country_block(block_lines)
    assert scan.flatten_frequency_blocks(freq_blocks) == [
        (2402, 2474),
        (5170, 5330),
        (5490, 5730),
        (5735, 5835),
        (57240, 63720),
    ]

def test_channel_list_unset(regdb_lines):
    block_lines = scan.get_country_rules_block("00", regdb_lines)
    freq_blocks = scan.get_frequencies_from_country_block(block_lines)
    freq_blocks = scan.flatten_frequency_blocks(freq_blocks)
    assert scan.get_channel_list_from_frequency_blocks(freq_blocks) == \
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

JP_REGDB = """\
country JP: DFS-JP
	(2402.000 - 2482.000 @ 40.000), (20.00), (N/A)
	(2474.000 - 2494.000 @ 20.000), (20.00), (N/A), NO-OFDM
	(4910.000 - 4990.000 @ 40.000), (23.00), (N/A)
	(5030.000 - 5090.000 @ 40.000), (23.00), (N/A)
	(5170.000 - 5250.000 @ 80.000), (20.00), (N/A), AUTO-BW
	(5250.000 - 5330.000 @ 80.000), (20.00), (N/A), DFS, AUTO-BW
	(5490.000 - 5710.000 @ 160.000), (23.00), (N/A), DFS
	(59000.000 - 66000.000 @ 2160.000), (10.00), (N/A)"""

def test_get_country_rules_block_jp(regdb_lines):
    block_lines = scan.get_country_rules_block("JP", regdb_lines)
    assert block_lines == JP_REGDB.split("\n")

def test_jp_freq_extraction(regdb_lines):
    block_lines = scan.get_country_rules_block("JP", regdb_lines)
    freq_blocks = scan.get_frequencies_from_country_block(block_lines)
    assert freq_blocks == [
        (2402, 2474),
        (4910, 4990),
        (5030, 5090),
        (5170, 5250),
        (5250, 5330),
        (5490, 5710),
        (59000, 66000),
    ]

def test_flattening_of_jp_freqs(regdb_lines):
    block_lines = scan.get_country_rules_block("JP", regdb_lines)
    freq_blocks = scan.get_frequencies_from_country_block(block_lines)
    assert scan.flatten_frequency_blocks(freq_blocks) == [
        (2402, 2474),
        (4910, 4990),
        (5030, 5090),
        (5170, 5330),
        (5490, 5710),
        (59000, 66000),
    ]

def test_get_country_rules_block_unmatched(regdb_lines):
    block_lines = scan.get_country_rules_block("NOMATCH", regdb_lines)
    assert not block_lines
