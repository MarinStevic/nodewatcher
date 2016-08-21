from django.utils.translation import ugettext_lazy as _

from nodewatcher.core.registry import fields as registry_fields, registration


class NetworkProfileConfig(registration.bases.NodeConfigRegistryItem):
    """
    Network profile.
    """

    profiles = registry_fields.RegistryMultipleChoiceField(
        'node.config', 'network.profile#profiles',
        blank=True, null=True, default=[],
        help_text=_("Selected network profiles affect how the node is configured when automatic defaults are enabled. In case defaults are disabled, selecting network profiles will have no effect."),
    )

    class RegistryMeta:
        form_weight = 25
        registry_id = 'network.profile'
        registry_section = _("Network Profile")
        registry_name = _("Network Profile")

# Register possible network profiles.
registration.point('node.config').register_choice('network.profile#profiles', registration.Choice('routing-over-wan', _("Routing over WAN port")))
registration.point('node.config').register_choice(
    'network.profile#profiles',
    registration.Choice(
        'backbone-with-uplink',
        _("Backbone node with uplink"),
        limited_to=('core.type#type', 'backbone'),
    )
)
registration.point('node.config').register_choice('network.profile#profiles', registration.Choice('nat-clients', _("Clients behind NAT")))
registration.point('node.config').register_choice('network.profile#profiles', registration.Choice('no-lan-bridge', _("Don't bridge LAN port with clients")))
registration.point('node.config').register_choice('network.profile#profiles', registration.Choice('mobile-uplink', _("Use a mobile interface for uplink")))
registration.point('node.config').register_choice('network.profile#profiles', registration.Choice('wifi-uplink', _("Use a wireless interface for uplink")))
registration.point('node.config').register_choice('network.profile#profiles', registration.Choice('no-wifi-ap', _("Disable wireless AP")))
registration.point('node.config').register_choice('network.profile#profiles', registration.Choice('no-wifi-mesh', _("Disable wireless mesh")))
registration.point('node.config').register_choice('network.profile#profiles', registration.Choice('hostname-essid', _("Use hostname as ESSID")))
registration.point('node.config').register_item(NetworkProfileConfig)
