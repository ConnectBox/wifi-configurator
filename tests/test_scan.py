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
