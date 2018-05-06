import uuid

from django.db import models
from django.utils.translation import ugettext_lazy as _

from . import validators as core_validators
from .registry import fields as registry_fields, registration


class Node(models.Model):
    """
    This class represents a single node in the network.
    """

    uuid = models.CharField(max_length=40, primary_key=True)

    def save(self, **kwargs):
        """
        Override save so we can generate UUIDs.
        """

        if not self.uuid:
            self.pk = str(uuid.uuid4())

        super(Node, self).save(**kwargs)

    def __unicode__(self):
        """
        Returns a string representation of this node.
        """

        # TODO: Should we make this extensible?
        #       So that other modules and change (for example, project module could add project to the string).
        # TODO: Can we assume that config and general module is always available?
        #       Is this already breaking the abstraction? Should even general config use an extension point?
        return getattr(self.config.core.general(), 'name', None) or self.uuid

    def get_absolute_url(self):
        # TODO: Should we make this extensible?
        from django.core.urlresolvers import reverse
        return reverse('DisplayComponent:node', kwargs={'pk': self.pk})


# Create registration point
registration.create_point(Node, 'config')


class GeneralConfig(registration.bases.NodeConfigRegistryItem):
    """
    General node configuration containing basic parameters about the
    node.
    """

    name = models.CharField(
        max_length=50,
        null=True,
        validators=[core_validators.NodeNameValidator()],
    )

    class Meta:
        app_label = 'core'

    class RegistryMeta:
        form_weight = 1
        registry_id = 'core.general'
        registry_section = _("General Configuration")
        registry_name = _("Basic Configuration")
        lookup_proxies = ['name']


registration.point('node.config').register_item(GeneralConfig)


class RouterIdConfig(registration.bases.NodeConfigRegistryItem):
    """
    Router identifier configuration.
    """

    router_id = models.CharField(max_length=100, editable=False)
    rid_family = registry_fields.RegistryChoiceField('node.config', 'core.routerid#family', editable=False)

    class Meta:
        app_label = 'core'

    class RegistryMeta:
        form_weight = 49
        registry_id = 'core.routerid'
        registry_section = _("Router Identifier")
        registry_name = _("Generic Router ID")
        multiple = True
        hidden = True


registration.point('node.config').register_choice('core.routerid#family', registration.Choice('ipv4', _("IPv4")))
registration.point('node.config').register_choice('core.routerid#family', registration.Choice('ipv6', _("IPv6")))
registration.point('node.config').register_item(RouterIdConfig)


class StaticIpRouterIdConfig(RouterIdConfig):
    """
    Static router identifier configuration.
    """

    address = registry_fields.IPAddressField(
        help_text=_(
            "A static IP address is not allocated from an IP pool. " +
            "A conflict with an IP allocated from an IP pool is possible. " +
            "Consider allocating it from the IP pool and use \"hint\" to suggest the wanted IP address."
        ),
    )

    class Meta:
        app_label = 'core'

    class RegistryMeta(RouterIdConfig.RegistryMeta):
        registry_name = _("Static IP Router ID")
        hidden = False

    def save(self, *args, **kwargs):
        self.full_clean()

        if self.address.version == 4:
            self.rid_family = 'ipv4'
        elif self.address.version == 6:
            self.rid_family = 'ipv6'

        self.router_id = str(self.address.ip)
        super(StaticIpRouterIdConfig, self).save(*args, **kwargs)


registration.point('node.config').register_item(StaticIpRouterIdConfig)
