#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `wifi_configurator` package."""

import sys
import unittest
from click.testing import CliRunner
import click
import pytest

from wifi_configurator import cli


class MockCtx:  # pylint: disable=too-few-public-methods
    def __init__(self, filename):
        self.params = {"filename": filename}


class TestWifi_configurator(unittest.TestCase):
    """Tests for `wifi_configurator` package."""

    def setUp(self):
        """Set up test fixtures, if any."""

    def tearDown(self):
        """Tear down test fixtures, if any."""

    @pytest.mark.skip(reason="Change filename to be an argument, not option.")
    def test_command_line_interface(self):
        """Test the CLI."""
        runner = CliRunner()
        result = runner.invoke(cli.main)
        self.assertEqual(result.exit_code, 0)
        self.assertIn('wifi_configurator.cli.main', result.output)
        help_result = runner.invoke(cli.main, ['--help'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn('--help   Show this message and exit.', help_result.output)

    @pytest.mark.skipif(sys.platform != "linux2",
                        reason="test requires regdbdump - linux only")
    def test_filename_dash_to_stdout(self):
        """Test taking config on stdin automatically writes to stdout"""
        runner = CliRunner()
        result = runner.invoke(
            cli.main,
            ['--filename', '-'],
            input='somekey=somevalue')
        self.assertFalse(result.exception)
        self.assertIn("interface=wlan0", result.output)

    @pytest.mark.skipif(sys.platform != "linux2",
                        reason="test requires regdbdump - linux only")
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

    @pytest.mark.skip(reason="Change filename to be an argument. Then handle missing file")
    def test_missing_filename_file(self):
        pass


    def test_wpa_passphrase_callback(self):
        ctx = MockCtx("junk.conf")
        wpa = cli.cb_handle_wpa_passphrase(ctx, "wpa_passphrase", None)
        # Default wpa_passphrase
        self.assertEqual(wpa, "")
        # use a fixture, luke...
        wpa = cli.cb_handle_wpa_passphrase(ctx, "wpa_passphrase", "")
        # Unset what was previously set
        self.assertEqual(wpa, "")
        wpa = cli.cb_handle_wpa_passphrase(ctx, "wpa_passphrase", "hellokit")
        # Unset what was previously set
        self.assertEqual(wpa, "hellokit")
        # Yell if the passphrase is too short
        self.assertRaises(
            click.BadParameter,
            cli.cb_handle_wpa_passphrase,
            ctx, "wpa_passphrase", "short"
        )
