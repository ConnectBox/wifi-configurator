import collections
from pathlib import Path
import subprocess
import re
import configobj
import pyric.pyw as pyw


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

def detect_regdomain(wlan_if):
    crda_config = Path("/etc/default/crda")
    c = configobj.ConfigObj(crda_config.as_posix())
    # Treat any REGDOMAIN setting in crda as a deliberate override
    regdomain = c.get("REGDOMAIN", "")
    if regdomain:
        return regdomain

    with ActiveWifiInterface(wlan_if) as awi:
        if not awi:
            return ""

        iw = subprocess.run([
            "iw",
            "dev",
            wlan_if.dev,
            "scan"
        ], capture_output=True)
        return get_consensus_regdomain_from_iw_output(iw.stdout)
