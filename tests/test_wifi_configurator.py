#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `wifi_configurator` package."""


import unittest
from click.testing import CliRunner

from wifi_configurator import wifi_configurator
from wifi_configurator import cli


class TestWifi_configurator(unittest.TestCase):
    """Tests for `wifi_configurator` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_000_something(self):
        """Test something."""

    def test_command_line_interface(self):
        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.main)
        assert result.exit_code == 0
        assert 'wifi_configurator.cli.main' in result.output
        help_result = runner.invoke(cli.main, ['--help'])
        assert help_result.exit_code == 0
        assert '--help  Show this message and exit.' in help_result.output
