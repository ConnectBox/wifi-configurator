import collections
import functools
from pathlib import Path
import subprocess
import re
import time
import click
import configobj
import pyric.pyw as pyw
import pyric.utils.channels as channels
import pprint

# OFDM. We don't use DSSS, so their 22MHz width doesn't matter
CHANNEL_WIDTH_MHZ_24 = 20
NO_CHANNEL = 0


class ActiveWifiInterface:

    STATE_ACTIVE = "up"
    STATE_INACTIVE = "down"

    def __init__(self, wlan_if):
        self.wlan_if = wlan_if
        if pyw.isup(self.wlan_if):
            self.initial_state = self.STATE_ACTIVE
        else:
            self.initial_state = self.STATE_INACTIVE

    def __enter__(self):
        if not pyw.isup(self.wlan_if):
            pyw.up(self.wlan_if)
            return True

        # Good to go if it's already active, but not otherwise
        return self.initial_state == self.STATE_ACTIVE

    def __exit__(self, *args):
        # Leave things the way you found them, like your parents said
        if self.initial_state == self.STATE_INACTIVE:
            pyw.down(self.wlan_if)


def get_country_count_from_iw_output(iw_output):
    c = collections.Counter()
    for line in iw_output.split("\n"):
        # e.g. '        Country: TR     Environment: Indoor/Outdoor
        line = line.strip()
        if not line.startswith("Country:"):
            continue

        fields = re.split(r'\s+', line)
        if len(fields) > 1:
            c[fields[1]] += 1

    return c


def get_consensus_regdomain_from_iw_output(iw_output):
    cnter = get_country_count_from_iw_output(iw_output)
    most_common = cnter.most_common(1)
    if most_common:
        return most_common[0][0]

    return ""


@functools.lru_cache()
def get_scan_output(wlan_if):
    with ActiveWifiInterface(wlan_if) as awi:
        if not awi:
            return ""
        a = ""
        b = 0
        while a == "" and b < 5:
            iw = subprocess.run([
                "/sbin/iw",
                "dev",
                wlan_if.dev,
                "scan"
            ], stdout=subprocess.PIPE)
            a = iw.stdout.decode("utf-8") 
            b += 1
            if a == "": time.sleep(2)
    return a


def get_freq_signal_tuples_from_iw_output(iw_output):
    freq_signal_tuples = []
    freq = 0
    signal = 0.0
    for line in iw_output.split("\n"):
        line = line.strip()
        if line.startswith("BSS"):
            # New BSS (or first one)
            if freq and signal:
                # It's a new BSS so process the last reading
                freq_signal_tuples.append((freq, signal))
            continue

        # freq: 2412
        if line.startswith("freq:"):
            _, freq_str = line.split(":")
            freq = int(freq_str)
            continue

        # signal: -48.00 dBm
        if line.startswith("signal:"):
            _, signal_str = line.split(":")
            signal = float(signal_str.strip().split(" ")[0])
            continue

    # Process the reading from the last BSS, assuming there was one
    if freq and signal:
        freq_signal_tuples.append((freq, signal))
    return freq_signal_tuples


def get_max_signal_at_each_freq(freq_signal_tuples):
    freq_signal_map = {}
    for freq, signal in freq_signal_tuples:
        if freq in freq_signal_map:
            if signal > freq_signal_map[freq]:
                freq_signal_map[freq] = signal
        else:
            freq_signal_map[freq] = signal


def channel_overlaps_with_others(channel, channel_list):
    # we don't care about overlaps at endpoints, so add 1 to the base
    # (range strips the top value anyway)
    freq_range = set(range(
        channels.ISM_24_C2F[channel] - (CHANNEL_WIDTH_MHZ_24 // 2) + 1,
        channels.ISM_24_C2F[channel] + (CHANNEL_WIDTH_MHZ_24 // 2)

    ))
    for item in channel_list:

        item_freq_range = set(range(
            channels.ISM_24_C2F[item] - (CHANNEL_WIDTH_MHZ_24 // 2) + 1,
            channels.ISM_24_C2F[item] + (CHANNEL_WIDTH_MHZ_24 // 2)
        ))
        if freq_range.intersection(item_freq_range):
            return True

    return False


def get_available_uncontested_channel(all_available_channels, scan_output):
    freq_signal_tuples = get_freq_signal_tuples_from_iw_output(scan_output)
    used_channels = [
        channels.ISM_24_F2C[freq] for freq, _ in freq_signal_tuples
        if freq in channels.ISM_24_F2C  # ignore non 2.4Ghz for the moment
    ]
    click.echo("Available channels are: %s" %
               (",".join([str(c) for c in all_available_channels])))
    click.echo("Used channels are: %s" %
               (",".join([str(c) for c in used_channels])))
    for channel in all_available_channels:
        if not channel_overlaps_with_others(channel, used_channels):
            return channel

    return NO_CHANNEL


def detect_regdomain(scan_output):
    crda_config = Path("/etc/default/crda")
    c = configobj.ConfigObj(crda_config.as_posix())
    # Treat any REGDOMAIN setting in crda as a deliberate override
    regdomain = c.get("REGDOMAIN", "")
    if regdomain:
        return regdomain
    return get_consensus_regdomain_from_iw_output(scan_output)


def get_country_rules_block(country_code, lines):
    in_country_block = False
    country_lines = []
    for line in lines:
        if in_country_block:
            if line.strip():
                country_lines.append(line)
                continue
            else:
                # We're at the end of the country block
                return country_lines
        elif (not (line.find(country_code) >=0)):
            continue
        in_country_block = True
        country_lines.append(line)
        continue
    return country_lines


def get_frequency_blocks_from_country_block(country_code, lines):
    freqency_blocks = []
    block_lower_point = 0
    block_upper_point = 0
    # Drop the line with the country definition
    frequency_lines = lines[1:]
    # example frequency line format
    # \t(2457.000 - 2482.000 @ 20.000), (20.00), (N/A), NO-IR, AUTO-BW
    for line in frequency_lines:
        # Dump leading whitespace,
        # grab everything to the left of the @
        # drop the first character (the paranthesis)
        freq_section = line.strip().split("@")[0][1:]
        new_block_lower_point, new_block_upper_point = [
            float(freq.strip()) for freq in freq_section.split("-")
        ]
        # We can't use a frequency marked as NO-OFDM, so we must
        #  drop them. This includes channel 14 in JP and 12+13 in 00
        # NO-OFDM may overlap with the range on the previous line (strictly
        #  speaking it could be many lines of overlap, but let's ignore that
        #  given there's only 00 and JP with NO-OFDM and that doesn't go back
        #  more than one line.
        if ("NO-OFDM" in line):
            # If the NO-OFDM line encroaches on the top end of the previous
            #  block, redefine the top of the previous block to be where the
            #  NO-OFDM block starts
            if new_block_lower_point < block_upper_point:
                block_upper_point = new_block_lower_point
            continue

        # Process the last block
        if block_lower_point and block_upper_point:
            freqency_blocks.append((block_lower_point, block_upper_point))

        # and remember this block for subsequent processing
        block_lower_point = new_block_lower_point
        block_upper_point = new_block_upper_point

    if block_lower_point and block_upper_point:
        freqency_blocks.append((block_lower_point, block_upper_point))
    click.echo("Frequency blocks are {}" )
    pprint.pprint(freqency_blocks)
    return freqency_blocks


def flatten_frequency_blocks(blocks):
    # We don't care for the power or band specific rules, so we can
    #  collapse the frequency ranges. regdb output is always sorted
    #  by increasing frequency, so we can make some assumptions about
    #  order as we're flattening
    flattened_blocks = []
    block_lower_point = 0
    block_upper_point = 0
    for start, end in blocks:
        if start > block_upper_point:
            # This block doesn't overlap with the last or extend it
            #  and isn't our starting point - flush the last block
            if block_lower_point > 0 and block_upper_point > 0:
                flattened_blocks.append((block_lower_point, block_upper_point))
            block_lower_point = start
            block_upper_point = end
        else:
            # This block continues or is completely enclosed in the block
            #  that we're processing
            if end > block_upper_point:
                # We're extending the block
                block_upper_point = end

    # flush the last oneO

    flattened_blocks.append((block_lower_point, block_upper_point))
    return flattened_blocks


def get_channel_list_from_frequency_blocks(freq_list):
    allowed_channels = []
    for channel, centre_freq in channels.ISM_24_C2F.items():
        for start, end in freq_list:
            # i.e. is the channel wholely contained in the block?
            if start <= centre_freq - (CHANNEL_WIDTH_MHZ_24 / 2) and \
                   centre_freq + (CHANNEL_WIDTH_MHZ_24 / 2) <= end:
                allowed_channels.append(channel)
    return allowed_channels


def channels_for_country(country_code):
    regdump = subprocess.run(["/sbin/regdbdump", "/lib/crda/regulatory.bin"],
                             stdout=subprocess.PIPE)
    lines = regdump.stdout.decode('utf-8').split("\n")
    country_rules_block = get_country_rules_block(country_code, lines)
    frequency_blocks = get_frequency_blocks_from_country_block(country_code, country_rules_block)
    frequency_blocks = flatten_frequency_blocks(frequency_blocks)
    return get_channel_list_from_frequency_blocks(frequency_blocks)
