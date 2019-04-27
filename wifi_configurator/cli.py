# -*- coding: utf-8 -*-

"""Console script for wifi_configurator."""
import functools
import os
import sys

import click
import configobj
import jinja2


SYSLOG_TAG = "wifi-configurator"
DEFAULT_SSID = "ConnectBox - Free Media"
DEFAULT_CHANNEL = "7"


@functools.lru_cache()
def hostapd_conf_as_config(filename):
    if os.path.exists(filename):
        return configobj.ConfigObj(filename)
    click.echo("Warning: unable to load specific config file: %s" %
               (filename,))
    return configobj.ConfigObj()

# The following get_current_... methods are crafted to take steps to recover
#  from a busted config file by defaulting to values that will allow hostapd
#  to start
def get_current_ssid(config):
    return config.get("ssid", DEFAULT_SSID)

def get_current_channel(config):
    return config.get("channel", DEFAULT_CHANNEL)

def get_current_ht_capab(config):
    return config.get("ht_capab", "")

def get_current_country_code(config):
    return config.get("country_code", "")

def get_current_ac_mode(config):
    return config.get("ieee80211ac", "0")


@click.command()
@click.option('-f', '--filename',
              default="/etc/hostapd/hostapd.conf",
              help="Input file to be used for values not being updated. "
                   "Defaults to /etc/hostapd/hostapd.conf")
@click.option('-i', '--interface',
              default="wlan0",
              help="Wifi interface name. Defaults to wlan0")
@click.option('-s', '--ssid',
              help="Set a new ssid for the access point")
@click.option('-c', '--channel',
              help="Set a new channel for the access point")
@click.option('-o', '--output',
             help="Destination for updated configuration file. "
                  "Defaults to filename. - writes to stdout")
def main(filename, interface, ssid, channel, output):
    """Console script for wifi_configurator."""
    if filename == "-":
        filename = sys.stdin
    config = hostapd_conf_as_config(filename)
    # Could use a callback and access filename parameter in the decorator,
    #  (filename possibly needs is_eager) or by subclassing click.Option
    #  (https://old.reddit.com/r/learnpython/comments/ah61cj/how_to_set_pythonclick_options_that_reference/eebxfah/) but let's get started
    if not ssid:
        ssid = get_current_ssid(config)
    if not channel:
        channel = get_current_channel(config)
    if not output:
        output = filename
    if output == "-":
        output = sys.stdout

    ht_capab = get_current_ht_capab(config)
    ac_mode = get_current_ac_mode(config)
    country_code = get_current_country_code(config)

    file_loader = jinja2.PackageLoader('wifi_configurator', 'templates')
    env = jinja2.Environment(loader=file_loader)
    template = env.get_template('hostapd.conf.j2')

    rendered = template.stream(
        interface=interface,
        ssid=ssid,
        channel=channel,
        country_code=country_code,
        ht_capab=ht_capab,
        ac_mode=ac_mode,
    )
    rendered.dump(output)
    return 0


#if __name__ == "__main__":
#    sys.exit(main())  # pragma: no cover
