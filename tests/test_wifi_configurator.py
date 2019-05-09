#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `wifi_configurator` package."""


import unittest
from click.testing import CliRunner

#from wifi_configurator import wifi_configurator
from wifi_configurator import cli


class TestWifi_configurator(unittest.TestCase):
    """Tests for `wifi_configurator` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    @unittest.skip("Change filename to be an argument, not option.")
    def test_command_line_interface(self):
        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.main)
        self.assertEqual(result.exit_code, 0)
        self.assertIn('wifi_configurator.cli.main', result.output)
        help_result = runner.invoke(cli.main, ['--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('--help   Show this message and exit.', help_result.output)

    def test_filename_dash_to_stdout(self):
        """Test taking config on stdin automatically writes to stdout"""
        runner = CliRunner()
        result = runner.invoke(
            cli.main,
            ['--filename', '-'],
            input='somekey=somevalue')
        self.assertFalse(result.exception)
        self.assertIn("interface=wlan0", result.output)

    def test_output_dash_to_stdout(self):
        """Test output = dash writes to stdout"""
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open('hostapd.conf', 'w') as f:
                f.write('somekey=somevalue')

            result = runner.invoke(
                cli.main,
                ['--output', '-'],
            )
            self.assertFalse(result.exception)
            self.assertIn("interface=wlan0", result.output)

    @unittest.skip("Change filename to be an argument. Then handle missing file")
    def test_missing_filename_file(self):
        pass
