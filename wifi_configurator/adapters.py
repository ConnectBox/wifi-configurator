# -*- coding: utf-8 -*-

import os
import configobj


class DefaultAdapter:
    ht_capab = ""
    vht_capab = ""
    ac_active = 0

    def __str__(self):
        return "Default wifi adapter"


class RTL8812AU:
    """RTL 8812AU 802.11ac"""
    PRODUCT_list = [
        "bda/8812/0",
        "bda/881a/0",
    ]
    # iw list reports "Static SM Power Save" in capabilities for
    #  this device, but hostapd is unable to start if SMPS-STATIC
    #  is set. It's unclear why and thus we exclude it.
    # Deliberately do not advertise 40Mhz channels even though they're
    #  supported because we never want to use them given rapid
    #  performance degradation under non-ideal conditions and the
    #  difficulty of configuration across regulatory domains
    # Note that RX-STBC1 is not available for 5GHz on this device
    #  so we may need to remove it if we enable that band.
    ht_capab = "[HT20][SHORT-GI-20][RX-STBC1][MAX-AMSDU-7935]"
    # None of the vht_capab advertised by the hardware (iw list) are
    #  supported (seemingly, by the driver)
    vht_capab = ""
    ac_active = 1

    def __str__(self):
        return "RTL 8812au 802.11ac wifi adapter"


class Realtek5372:
    """
    Realtek 5372 (external USB shipped with Neo Connectbox)
    """
    PRODUCT = "148f/5372/101"
    # Realtek 5372 (external USB shipped with Neo Connectbox)dd
    # Deliberately do not advertise 40Mhz channels even though they're
    #  supported because we never want to use them given rapid
    #  performance degradation under non-ideal conditions and the
    #  difficulty of configuration across regulatory domains
    ht_capab = "[HT20][GF][SHORT-GI-20][TX-STBC][RX-STBC12]"

    def __str__(self):
        return "Realtek 5372 802.11n wifi adapter"

class MT7601:
    """
    Media Teck 7601U (eternal USB shipped with Neo Connectbox for Client Side)
    """
    PRODUCT = "148f/7601/100"
    #Media Teck (external USB shipped with NEO Connectbox)
    WirelessMode = 5
    # Set Wireless Mode to 11ABGN mixed
    ht_capab = "[HT20][SHORT-GI-20][HT40]"
    vht_capab = ""
    ac_active = 0
    
    def __str__(self):
        return "Media Teck 7601U series 802.11n wifi adapter"
        
        
class BCM4343x:
    """
    Broadcom 4343x series

    BCM43438 is a part of BCM2835 on RPi0w
    BCM43438 is part of the BCM2837 on RPi3b
    BCM43430 is a part of the AP6212 on OPi0+2
    """
    SDIO_ID = "02D0:A9A6"
    # iw list reports "Static SM Power Save" in capabilities for
    #  this device, but hostapd is unable to start if SMPS-STATIC
    #  is set. It's unclear why and thus we exclude it.
    ht_capab = "[HT20][SHORT-GI-20][DDDS_CCK-40]"
    vht_capab = ""
    ac_active = 0

    def __str__(self):
        return "Broadcom 4343x series 802.11n wifi adapter"


class BCM43455:
    """
    Broadcom 43455 series

    Cypress43455 is a rebadged BCM43455 and is on RPi3b+

    Currently indistinguishable from BCM4343x, which is confusing given
    this chipset is actually 802.11ac capable
    """

    def __str__(self):
        return "Broadcom 43455 series 802.11ac wifi adapter"


def factory(interface):
    uevent_file = os.path.join(
        "/sys/class/net",
        interface,
        "device/uevent"
    )
    if not os.path.exists(uevent_file):
        # Be conservative... we can't be sure what's going on
        return DefaultAdapter()

    config = configobj.ConfigObj(uevent_file)
    if config.get("SDIO_ID") == BCM4343x.SDIO_ID:
        return BCM4343x()

    if config.get("PRODUCT") == Realtek5372.PRODUCT:
        return Realtek5372()

    if config.get("PRODUCT") in RTL8812AU.PRODUCT_list:
        return RTL8812AU()

    # Can't identify the adapter. Let's be conservative
    return DefaultAdapter()
