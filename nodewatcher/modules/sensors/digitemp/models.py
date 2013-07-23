from django.utils.translation import ugettext as _

from nodewatcher.core.generator.cgm import models as cgm_models
from nodewatcher.core.registry import registration


class DigitempPackageConfig(cgm_models.PackageConfig):
    """
    Common configuration for CGM packages.
    """
    # No fields

    class RegistryMeta(cgm_models.PackageConfig.RegistryMeta):
        registry_name = _("Digitemp")

registration.point('node.config').register_item(DigitempPackageConfig)
