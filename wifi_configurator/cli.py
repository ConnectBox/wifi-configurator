# -*- coding: utf-8 -*-
"""Console script for wifi_configurator."""
import functools
import os
import random
import subprocess
import sys
import json
import click
import configobj
import jinja2
import pyric
import pyric.pyw as pyw

from . import adapters
from . import scan


SYSLOG_TAG = "wifi-configurator"
DEFAULT_SSID = " - Free Media"
DEFAULT_CHANNEL = "7"


@functools.lru_cache()
def hostapd_conf_as_config(filename):
    if filename == sys.stdin or os.path.exists(filename):
        return configobj.ConfigObj(filename)
    click.echo("Warning: unable to load specific config file: %s" %
               (filename,))
    return configobj.ConfigObj()


# The following get_current_... methods are crafted to take steps to recover
#  from a busted config file by defaulting to values that will allow hostapd
#  to start
def get_current_ssid(config):
# Using a dictionary and json to store Branding stuff
# Read the dictionary
  with open('/usr/local/connectbox/brand.txt') as f:
    data = f.read()
    f.close()
    js = json.loads(data)
    brand_name = js["Brand"]
  return config.get("ssid", (brand_name + DEFAULT_SSID))


def get_current_channel(config):
    return int(config.get("channel", DEFAULT_CHANNEL))


def get_current_ht_capab(config):
    return config.get("ht_capab", "")


def get_current_country_code(config):
    return config.get("country_code", "")

def get_current_ac_mode(config):
    return config.get("ieee80211ac", "0")


def get_current_wpa_passphrase(config):
    # If it's not set, then pass back an empty string and we can follow
    #  the logic as if we're turning off password protection
    return config.get("wpa_passphrase", "")


def cb_handle_wpa_passphrase(ctx, _, value):
    # IF the passphrase is None, re-use whatever is already in config
    # We can't do a basic equality check here, because an empty string is
    #  used to disable password protection, and that's different to not
    #  specifying a wpa_passphrase (which is None when it's unset)
    if value is None:
        config = hostapd_conf_as_config(ctx.params["filename"])
        return get_current_wpa_passphrase(config)

    # An empty passphrase disables password auth so it's valid
    if value == "":
        return value

    # Otherwise, valid WPA passphrases are between 8 and 63 chars inclusive
    if 8 <= len(value) <= 63:
        return value

    raise click.BadParameter('Passphrase must be 8-63 characters long or empty')


def cb_handle_filename(_, _2, value):
    if value == "-":
        return sys.stdin

    return value


def cb_handle_output(ctx, _, value):
    if not value:
        if ctx.params["filename"] == sys.stdin:
            return sys.stdout

        return ctx.params["filename"]

    # If we read the config on stdin, we need a diff place to write the output
    if value == "-":
        return sys.stdout

    return value


@click.command()
# This must be an eager option because other options reference it in their
#  callbacks
@click.option('-f', '--filename',
              callback=cb_handle_filename,
              default="/etc/hostapd/hostapd.conf",
              is_eager=True,
              help="Input file to be used for values not being updated. "
                   "Defaults to /etc/hostapd/hostapd.conf")
@click.option('-i', '--interface',
              default="wlan0",
              help="Wifi interface name. Defaults to wlan0")
# Add length check (32 octets)
@click.option('-s', '--ssid',
              help="Set a new ssid for the access point")
# Add validation (possibly even taking region into account)
@click.option('-c', '--channel',
              type=int,
              help="Set a new channel for the access point")
@click.option('-o', '--output',
              callback=cb_handle_output,
              help="Destination for updated configuration file. "
                   "Defaults to filename. - writes to stdout")
@click.option('-p', '--wpa-passphrase',
              callback=cb_handle_wpa_passphrase,
              help="Access point passphrase (8-63 characters long). "
                   "Empty passphrase makes the access point open")
@click.option('--set-country-code',
              is_flag=True,
              help="Do a best-effort attempt to infer the local country "
                   "code by sniffing for other APs")
@click.option('--sync/--no-sync',
              default=True,
              help="Performs a filesystem sync after writing changes")
# pylint: disable=too-many-arguments,too-many-locals
def main(filename, interface, ssid, channel, output, wpa_passphrase, sync,
         set_country_code):
    """Console script for wifi_configurator."""
    config = hostapd_conf_as_config(filename)
    # Could use a callback and access filename parameter in the decorator,
    #  (filename possibly needs is_eager) or by subclassing click.Option
    if not ssid:
        ssid = get_current_ssid(config)

    wifi_adapter = adapters.factory(interface)
    # We deliberately only instantiate pyw.getcard for as small a set of
    #  parameters as possible because pyw gets sad if operations are
    #  attempted on a device that does not support nl80211 and we want to
    #  be to do as many things as possible in simulations
    scan_output = ""
    if set_country_code or not channel:
        try:
            if pyw.iswireless(interface):
                wlan_if = pyw.getcard(interface)
                scan_output = scan.get_scan_output(wlan_if)
            else:
                click.echo("Interface %s is not a wifi interface. Won't be "
                           "able to infer country code or do automatic "
                           "channel selection" % (interface,))
        except pyric.error:
            click.echo("Unable to query interface %s with pyw. Won't be "
                       "able to infer country code or do automatic "
                       "channel selection" % (interface,))

    # Retrieve the previous cc now, given we have so many fallback cases
    country_code = get_current_country_code(config)
    if set_country_code:
        scanned_cc = scan.detect_regdomain(scan_output)
        # Only use the scanned cc if it's non-empty
        if scanned_cc:
            country_code = scanned_cc
        else:
            click.echo("Could not do wifi scan. Using previous country code")

    valid_channels_for_cc = scan.channels_for_country(country_code)
    if not channel:
        # Choose an uncontested channel, or a random one if there aren't any
        # MEH that we respecify wlan_if when we've used it to scan just a bit
        #  earlier
        channel = scan.get_available_uncontested_channel(
            valid_channels_for_cc, scan_output
        )
        if not channel:
            channel = random.choice(valid_channels_for_cc)
            click.echo("No uncontested channels. Choosing %s at random" %
                       (channel,))
        else:
            click.echo("Channel %s is uncontested and is now the new channel" %
                       (channel,))
        channel = get_current_channel(config)
        if channel not in valid_channels_for_cc:
            click.echo("Channel %s is not valid for new country code %s. "
                       "Setting channel to %s" % (channel, country_code,
                                                  valid_channels_for_cc[0]))
            channel = valid_channels_for_cc[0]
    else:
        if channel not in valid_channels_for_cc:
            raise click.BadParameter(
                "Channel %s is not valid for country code %s. Valid choices "
                "are %s. Exiting" % (
                    channel,
                    country_code,
                    ",".join([str(i) for i in valid_channels_for_cc])))

    file_loader = jinja2.PackageLoader('wifi_configurator')
    env = jinja2.Environment(
        loader=file_loader,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template('hostapd.conf.j2')
    rendered = template.stream(
        interface=interface,
        ssid=ssid,
        channel=channel,
        country_code=country_code,
        wifi_adapter=wifi_adapter,
        wpa_passphrase=wpa_passphrase,
    )
    rendered.dump(output)
    # Some filesystems don't write to disk for a while, which can lead to
    #  corruption in files. A corrupt hostapd.conf may well brick a device
    #  in the field so let's avoid that risk.
    # Related: https://github.com/ConnectBox/connectbox-pi/issues/220
    if sync and output != sys.stdout:
        subprocess.run("/bin/sync")
    return 0


if __name__ == "__main__":
    main()
