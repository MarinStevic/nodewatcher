from nodewatcher.core.generator.cgm import base as cgm_base, protocols as cgm_protocols, devices as cgm_devices


class TPLinkWR741NDv1(cgm_devices.DeviceBase):
    """
    TP-Link WR741NDv1 device descriptor.
    """

    identifier = 'tp-wr741ndv1'
    name = "WR741ND (v1)"
    manufacturer = "TP-Link"
    url = 'http://www.tp-link.com/'
    architecture = 'ar71xx'
    radios = [
        cgm_devices.IntegratedRadio('wifi0', "Integrated wireless radio", [
            cgm_protocols.IEEE80211BGN(
                cgm_protocols.IEEE80211BGN.SHORT_GI_20,
                cgm_protocols.IEEE80211BGN.SHORT_GI_40,
                cgm_protocols.IEEE80211BGN.RX_STBC1,
                cgm_protocols.IEEE80211BGN.DSSS_CCK_40,
            )
        ], [
            cgm_devices.AntennaConnector('a1', "Antenna0")
        ], [
            cgm_devices.DeviceRadio.MultipleSSID,
        ])
    ]
    switches = [
        cgm_devices.Switch(
            'sw0', "Switch0",
            ports=5,
            cpu_port=0,
            vlans=16,
        )
    ]
    ports = [
        cgm_devices.EthernetPort('wan0', "Wan0"),
        cgm_devices.SwitchedEthernetPort(
            'lan0', "Lan0",
            switch='sw0',
            vlan=1,
            ports=[0, 1, 2, 3, 4],
        )
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
            'sw0': 'switch0',
            'wan0': 'eth1',
            'lan0': 'eth0',
        }
    }
    drivers = {
        'openwrt': {
            'wifi0': 'mac80211'
        }
    }
    profiles = {
        'openwrt': {
            'name': 'TLWR741',
            'files': [
                'openwrt-ar71xx-generic-tl-wr741nd-v1-squashfs-factory.bin',
                'openwrt-ar71xx-generic-tl-wr741nd-v1-squashfs-sysupgrade.bin'
            ]
        }
    }


class TPLinkWR741NDv2(TPLinkWR741NDv1):
    """
    TP-Link WR741NDv2 device descriptor.
    """

    identifier = 'tp-wr741ndv2'
    name = "WR741ND (v2)"
    profiles = {
        'openwrt': {
            'name': 'TLWR741',
            'files': [
                'openwrt-ar71xx-generic-tl-wr741nd-v2-squashfs-factory.bin',
                'openwrt-ar71xx-generic-tl-wr741nd-v2-squashfs-sysupgrade.bin'
            ]
        }
    }


class TPLinkWR741NDv4(TPLinkWR741NDv1):
    """
    TP-Link WR741NDv4 device descriptor.
    """

    identifier = 'tp-wr741ndv4'
    name = "WR741ND (v4)"
    profiles = {
        'openwrt': {
            'name': 'TLWR741',
            'files': [
                'openwrt-ar71xx-generic-tl-wr741nd-v4-squashfs-factory.bin',
                'openwrt-ar71xx-generic-tl-wr741nd-v4-squashfs-sysupgrade.bin'
            ]
        }
    }

# Register the TP-Link WR741ND devices.
cgm_base.register_device('openwrt', TPLinkWR741NDv1)
cgm_base.register_device('openwrt', TPLinkWR741NDv2)
cgm_base.register_device('openwrt', TPLinkWR741NDv4)
