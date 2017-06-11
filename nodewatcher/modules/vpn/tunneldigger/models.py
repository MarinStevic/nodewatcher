import datetime

from django.apps import apps
from django.contrib.postgres import fields as postgres_fields
from django.db import models
from django.utils.translation import ugettext_lazy as _, ugettext

from polymorphic import models as polymorphic_models

from nodewatcher.core import validators as core_validators
from nodewatcher.core.registry import fields as registry_fields, registration
from nodewatcher.core.generator.cgm import models as cgm_models


class TunneldiggerServer(polymorphic_models.PolymorphicModel):
    """
    Tunneldigger server configuration.
    """

    name = models.CharField(max_length=100)
    address = registry_fields.IPAddressField(host_required=True)
    ports = postgres_fields.ArrayField(
        models.IntegerField(validators=[core_validators.PortNumberValidator()])
    )
    enabled = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("Tunneldigger server")

    def __unicode__(self):
        return u"%s (%s)" % (self.name, self.address)

# In case projects module is installed, we support per-project server configuration.
if apps.is_installed('nodewatcher.modules.administration.projects'):
    from nodewatcher.modules.administration.projects import models as projects_models

    class PerProjectTunneldiggerServer(TunneldiggerServer):
        project = models.ForeignKey(projects_models.Project, related_name='+')

        class Meta:
            verbose_name = _("Project-specific tunneldigger server")


class TunneldiggerInterfaceConfig(cgm_models.InterfaceConfig, cgm_models.RoutableInterface):
    """
    Tunneldigger VPN interface.
    """

    mac = registry_fields.MACAddressField(auto_add=True)
    server = registry_fields.ModelRegistryChoiceField(TunneldiggerServer, limit_choices_to={'enabled': True})
    uplink_interface = registry_fields.ReferenceChoiceField(
        cgm_models.InterfaceConfig,
        # Limit choices to interfaces selected as uplinks.
        limit_choices_to=lambda model: getattr(model, 'uplink', False),
        related_name='+',
        help_text=_("Select this if you want to bind the tunnel only to a specific interface."),
    )

    class RegistryMeta(cgm_models.InterfaceConfig.RegistryMeta):
        registry_name = _("Tunneldigger Interface")

    def __unicode__(self):
        if not self.server:
            return ugettext("Tunneldigger interface (no server)")

        return ugettext("Tunneldigger interface (%(server)s)") % {'server': self.server}

registration.point('node.config').register_item(TunneldiggerInterfaceConfig)

# Support QoS on tunneldigger interfaces.
if apps.is_installed('nodewatcher.modules.qos.base'):
    from nodewatcher.modules.qos.base import models as qos_models

    registration.point('node.config').register_subitem(
        TunneldiggerInterfaceConfig,
        qos_models.InterfaceQoSConfig,
    )


def get_tunneldigger_interface_name(index):
    """
    Returns the interface name of a tunneldigger interface with a specific
    index.

    :param index: Interface index
    """

    return "digger%d" % index


class TunneldiggerBrokerConfig(cgm_models.PackageConfig, cgm_models.RoutableInterface):
    """
    Tunneldigger broker configuration.
    """

    uplink_interface = registry_fields.ReferenceChoiceField(
        cgm_models.InterfaceConfig,
        # Limit choices to interfaces selected as uplinks.
        limit_choices_to=lambda model: getattr(model, 'uplink', False),
        related_name='+',
        help_text=_("Select on which interface the broker should listen on."),
    )
    ports = postgres_fields.ArrayField(
        models.IntegerField(validators=[core_validators.PortNumberValidator()])
    )
    max_cookies = models.PositiveIntegerField(default=1024)
    max_tunnels = models.PositiveIntegerField(default=1024)
    tunnel_timeout = models.DurationField(
        default=datetime.timedelta(minutes=1),
        verbose_name=_("Tunnel Timeout"),
        choices=(
            (datetime.timedelta(minutes=1), _("1 minute")),
            (datetime.timedelta(minutes=2), _("2 minutes")),
            (datetime.timedelta(minutes=5), _("5 minutes")),
        )
    )
    pmtu_discovery = models.BooleanField(
        default=True,
        verbose_name=_("Enable PMTU Discovery"),
    )

    class RegistryMeta(cgm_models.PackageConfig.RegistryMeta):
        registry_name = _("Tunneldigger Broker")

registration.point('node.config').register_item(TunneldiggerBrokerConfig)


def get_tunneldigger_broker_interface_name(mtu):
    """
    Returns the interface name of a tunneldigger interface with a specific
    MTU.

    :param mtu: Interface MTU
    """

    return "tdin%d" % mtu
