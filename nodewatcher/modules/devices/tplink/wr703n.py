from django.utils.translation import ugettext_lazy as _

from nodewatcher.core.generator.cgm import base as cgm_base, protocols as cgm_protocols, devices as cgm_devices


class TPLinkWR703Nv1(cgm_devices.DeviceBase):
    """
    TP-Link WR703Nv1 device descriptor.
    """

    identifier = 'tp-wr703nv1'
    name = "WR703N (v1)"
    manufacturer = "TP-Link"
    url = 'http://www.tp-link.com/'
    architecture = 'ar71xx_tiny'
    usb = True
    radios = [
        cgm_devices.IntegratedRadio('wifi0', _("Integrated wireless radio"), [
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
    ]
    ports = [
        cgm_devices.EthernetPort('wan0', "Wan0"),
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
        }
    }
    drivers = {
        'openwrt': {
            'wifi0': 'mac80211'
        }
    }
    profiles = {
        'openwrt': {
            'name': 'TLWR703',
            'files': [
                '*-ar71xx-generic-tl-wr703n-v1-squashfs-factory.bin',
                '*-ar71xx-generic-tl-wr703n-v1-squashfs-sysupgrade.bin'
            ]
        },
        'lede': {
            'name': 'tl-wr703n-v1',
            'files': [
                '*-ar71xx-tiny-tl-wr703n-v1-squashfs-factory.bin',
                '*-ar71xx-tiny-tl-wr703n-v1-squashfs-sysupgrade.bin'
            ]
        }
    }

# Register the TP-Link WR703N device
cgm_base.register_device('openwrt', TPLinkWR703Nv1)
