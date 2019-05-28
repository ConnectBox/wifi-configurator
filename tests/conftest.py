#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pathlib
import pytest

@pytest.fixture
def iw_dev_scan_0():
    p = pathlib.Path("tests/fixtures/iw_dev_scan_0.txt")
    return p.read_text()

@pytest.fixture
def iw_dev_scan_1():
    p = pathlib.Path("tests/fixtures/iw_dev_scan_1.txt")
    return p.read_text()

@pytest.fixture
def iw_dev_scan_2():
    p = pathlib.Path("tests/fixtures/iw_dev_scan_2.txt")
    return p.read_text()

@pytest.fixture
def iw_dev_scan_3():
    # This has tabs instead of spaces
    p = pathlib.Path("tests/fixtures/iw_dev_scan_3.txt")
    return p.read_text()

@pytest.fixture
def regdb_lines():
    p = pathlib.Path("tests/fixtures/reg-db.txt")
    return p.read_text().split("\n")
