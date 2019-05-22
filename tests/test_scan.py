#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pathlib
import unittest
from wifi_configurator import scan


class TestScan(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_get_country_count_populated(self):
        p = pathlib.Path("tests/fixtures/iw_dev_scan_0.txt")
        test_output = p.read_text()
        c = scan.get_country_count_from_iw_output(test_output)
        self.assertEqual(c.most_common(1)[0][0], "TR")
        self.assertEqual(len(list(c.elements())), 4)
        self.assertEqual(c["AL"], 1)

    def test_get_country_count_unpopulated(self):
        p = pathlib.Path("tests/fixtures/iw_dev_scan_1.txt")
        test_output = p.read_text()
        c = scan.get_country_count_from_iw_output(test_output)
        self.assertEqual(c.most_common(1), [])
        self.assertEqual(len(list(c.elements())), 0)

    def test_get_country_count_empty(self):
        p = pathlib.Path("tests/fixtures/iw_dev_scan_2.txt")
        test_output = p.read_text()
        c = scan.get_country_count_from_iw_output(test_output)
        self.assertEqual(c.most_common(1), [])
        self.assertEqual(len(list(c.elements())), 0)

    def test_get_country_count_populated2(self):
        # This has tabs instead of spaces
        p = pathlib.Path("tests/fixtures/iw_dev_scan_3.txt")
        test_output = p.read_text()
        c = scan.get_country_count_from_iw_output(test_output)
        self.assertEqual(c.most_common(1)[0][0], "AU")
        self.assertEqual(len(list(c.elements())), 2)
