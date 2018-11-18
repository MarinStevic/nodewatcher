from django.utils.translation import ugettext_lazy as _

from nodewatcher.core.generator.cgm import base as cgm_base, protocols as cgm_protocols, devices as cgm_devices


class UBNTNanoM2(cgm_devices.DeviceBase):
    """
    UBNT Nanostation M2 device descriptor.
    """

    identifier = 'ub-nano-m2'
    name = "Nanostation M2"
    manufacturer = "Ubiquiti"
    url = 'http://www.ubnt.com/'
    architecture = 'ar71xx_generic'
    radios = [
        cgm_devices.IntegratedRadio('wifi0', _("Integrated wireless radio"), [
            cgm_protocols.IEEE80211BGN(
                cgm_protocols.IEEE80211BGN.SHORT_GI_40,
                cgm_protocols.IEEE80211BGN.TX_STBC1,
                cgm_protocols.IEEE80211BGN.RX_STBC1,
                cgm_protocols.IEEE80211BGN.DSSS_CCK_40,
            )
        ], [
            cgm_devices.AntennaConnector('a1', "Antenna0")
        ], [
            cgm_devices.DeviceRadio.MultipleSSID,
        ])
    ]
    switches = []
    ports = [
        cgm_devices.EthernetPort('wan0', "Secondary"),
        cgm_devices.EthernetPort('lan0', "Primary"),
    ]
    antennas = [
        # TODO: This information is probably not correct
        cgm_devices.InternalAntenna(
            identifier='a1',
            polarization='horizontal',
            angle_horizontal=360,
            angle_vertical=75,
            gain=2,
        )
    ]
    port_map = {
        'openwrt': {
            'wifi0': 'radio0',
            'wan0': 'eth0',
            'lan0': 'eth1',
        }
    }
    drivers = {
        'openwrt': {
            'wifi0': 'mac80211'
        }
    }
    profiles = {
        'openwrt': {
            'name': 'UBNT',
            'files': [
                '*-ar71xx-generic-ubnt-nano-m-squashfs-factory.bin',
                '*-ar71xx-generic-ubnt-nano-m-squashfs-sysupgrade.bin',
            ]
        },
        'lede': {
            'name': 'ubnt-nano-m',
            'files': [
                '*-ar71xx-generic-ubnt-nano-m-squashfs-factory.bin',
                '*-ar71xx-generic-ubnt-nano-m-squashfs-sysupgrade.bin',
            ]
        }
    }


class UBNTNanoM5(UBNTNanoM2):
    """
    UBNT Nanostation M5 device descriptor.
    """

    identifier = 'ub-nano-m5'
    name = "Nanostation M5"
    radios = [
        cgm_devices.IntegratedRadio('wifi0', _("Integrated wireless radio"), [
            cgm_protocols.IEEE80211AN(
                cgm_protocols.IEEE80211AN.SHORT_GI_40,
                cgm_protocols.IEEE80211AN.TX_STBC1,
                cgm_protocols.IEEE80211AN.RX_STBC1,
                cgm_protocols.IEEE80211AN.DSSS_CCK_40,
            )
        ], [
            cgm_devices.AntennaConnector('a1', "Antenna0")
        ], [
            cgm_devices.DeviceRadio.MultipleSSID,
        ])
    ]


class UBNTNanoM5XW(UBNTNanoM5):
    """
    UBNT Nano M5 XW device descriptor.
    """

    identifier = 'ub-nano-m5-xw'
    name = "Nanostation M5 XW"
    profiles = {
        'openwrt': {
            'name': 'UBNT',
            'files': [
                '*-ar71xx-generic-ubnt-nano-m-xw-squashfs-factory.bin',
                '*-ar71xx-generic-ubnt-nano-m-xw-squashfs-sysupgrade.bin',
            ]
        },
        'lede': {
            'name': 'ubnt-nano-m-xw',
            'files': [
                '*-ar71xx-generic-ubnt-nano-m-xw-squashfs-factory.bin',
                '*-ar71xx-generic-ubnt-nano-m-xw-squashfs-sysupgrade.bin',
            ]
        }
    }


class UBNTLocoM2(UBNTNanoM2):
    """
    UBNT Nanostation Loco M2 device descriptor.
    """

    identifier = 'ub-loco-m2'
    name = "Nanostation Loco M2"
    ports = [
        cgm_devices.EthernetPort('lan0', "Lan0"),
    ]
    port_map = {
        'openwrt': {
            'wifi0': 'radio0',
            'lan0': 'eth0',
        }
    }


class UBNTLocoM5(UBNTNanoM5):
    """
    UBNT Nanostation Loco M5 device descriptor.
    """

    identifier = 'ub-loco-m5'
    name = "Nanostation Loco M5"
    ports = [
        cgm_devices.EthernetPort('lan0', "Lan0"),
    ]
    port_map = {
        'openwrt': {
            'wifi0': 'radio0',
            'lan0': 'eth0',
        }
    }


class UBNTLocoM5XW(UBNTLocoM5):
    """
    UBNT Nanostation Loco M5 XW device descriptor.
    """

    identifier = 'ub-loco-m5-xw'
    name = "Nanostation Loco M5 XW"
    profiles = {
        'openwrt': {
            'name': 'UBNT',
            'files': [
                '*-ar71xx-generic-ubnt-loco-m-xw-squashfs-factory.bin',
                '*-ar71xx-generic-ubnt-loco-m-xw-squashfs-sysupgrade.bin',
            ]
        },
        'lede': {
            'name': 'ubnt-loco-m-xw',
            'files': [
                '*-ar71xx-generic-ubnt-loco-m-xw-squashfs-factory.bin',
                '*-ar71xx-generic-ubnt-loco-m-xw-squashfs-sysupgrade.bin',
            ]
        }
    }


class UBNTNanobridgeM5(UBNTLocoM5):
    """
    UBNT Nanobridge M5 device descriptor.
    """

    identifier = 'ub-nanobridge-m5'
    name = "Nanobridge M5"


class UBNTNanobridgeM2(UBNTLocoM2):
    """
    UBNT Nanobridge M2 device descriptor.
    """

    identifier = 'ub-nanobridge-m2'
    name = "Nanobridge M2"


class UBNTLoco5AC(cgm_devices.DeviceBase):
    """
    UBNT NanoStation Loco5AC device descriptor.
    """

    identifier = 'ub-loco-5ac'
    name = "NanoStation Loco5AC"
    manufacturer = "Ubiquiti"
    url = 'http://www.ubnt.com/'
    architecture = 'ath79_generic'
    radios = [
        cgm_devices.IntegratedRadio('wifi0', _("Integrated wireless radio (5 GHz)"), [
            cgm_protocols.IEEE80211AC(
                cgm_protocols.IEEE80211AC.SHORT_GI_20,
                cgm_protocols.IEEE80211AC.SHORT_GI_40,
                cgm_protocols.IEEE80211AC.RX_STBC1,
                cgm_protocols.IEEE80211AC.DSSS_CCK_40,
            )
        ], [
            cgm_devices.AntennaConnector('a1', "Antenna1")
        ], [
            cgm_devices.DeviceRadio.MultipleSSID,
        ]),
        cgm_devices.IntegratedRadio('wifi1', _("Integrated wireless radio (2.4 GHz)"), [
            cgm_protocols.IEEE80211BGN(
                cgm_protocols.IEEE80211BGN.SHORT_GI_20,
                cgm_protocols.IEEE80211BGN.SHORT_GI_40,
                cgm_protocols.IEEE80211BGN.RX_STBC1,
                cgm_protocols.IEEE80211BGN.DSSS_CCK_40,
            )
        ], [
            cgm_devices.AntennaConnector('a2', "Antenna2")
        ], [
            cgm_devices.DeviceRadio.MultipleSSID,
        ])
    ]
    switches = []
    ports = [
        cgm_devices.EthernetPort('lan0', "Lan0")
    ]
    antennas = [
        # TODO: This information is probably not correct
        cgm_devices.InternalAntenna(
            identifier='a1',
            polarization='horizontal',
            angle_horizontal=360,
            angle_vertical=75,
            gain=2,
        ),
        # TODO: This information is probably not correct
        cgm_devices.InternalAntenna(
            identifier='a2',
            polarization='horizontal',
            angle_horizontal=360,
            angle_vertical=75,
            gain=2,
        )
    ]
    port_map = {
        'openwrt': {
            'wifi0': 'radio0',
            'wifi1': 'radio1',
            'lan0': 'eth0',
        }
    }
    drivers = {
        'openwrt': {
            'wifi0': 'mac80211',
            'wifi1': 'mac80211',
        }
    }
    profiles = {
        'lede': {
            'name': 'ubnt_nanostation-ac-loco',
            'files': [
                '*-ath79-generic-ubnt_nanostation-ac-loco-squashfs-factory.bin',
                '*-ath79-generic-ubnt_nanostation-ac-loco-squashfs-sysupgrade.bin',
            ]
        }
    }


# Register the UBNT Nano devices.
cgm_base.register_device('openwrt', UBNTNanoM2)
cgm_base.register_device('openwrt', UBNTNanoM5)
cgm_base.register_device('openwrt', UBNTNanoM5XW)
cgm_base.register_device('openwrt', UBNTLocoM2)
cgm_base.register_device('openwrt', UBNTLocoM5)
cgm_base.register_device('openwrt', UBNTLocoM5XW)
cgm_base.register_device('openwrt', UBNTNanobridgeM5)
cgm_base.register_device('openwrt', UBNTNanobridgeM2)
cgm_base.register_device('lede', UBNTLoco5AC)
