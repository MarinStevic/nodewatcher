from django import dispatch
from django.db import models
from django.utils.translation import gettext_noop

from nodewatcher.core.registry import registration
from nodewatcher.modules.monitor.datastream import fields as ds_fields, models as ds_models
from nodewatcher.modules.monitor.datastream.pool import pool as ds_pool


class SFPMonitor(registration.bases.NodeMonitoringRegistryItem):
    """
    SFP reported data.
    """

    serial_number = models.CharField(max_length=100)
    last_updated = models.DateTimeField(auto_now=True)
    bus = models.CharField(max_length=50)
    manufacturer = models.CharField(max_length=50)
    revision = models.CharField(max_length=50)
    type = models.IntegerField()
    connector = models.IntegerField()
    bitrate = models.IntegerField()
    wavelength = models.IntegerField()
    # SFP module diagnostics.
    temperature = models.FloatField(null=True)
    vcc = models.FloatField(null=True)
    tx_bias = models.FloatField(null=True)
    tx_power = models.FloatField(null=True)
    rx_power = models.FloatField(null=True)

    class RegistryMeta:
        registry_id = 'irnas.sfp'
        multiple = True

registration.point('node.monitoring').register_item(SFPMonitor)


class SFPMonitorStreams(ds_models.RegistryItemStreams):
    temperature = ds_fields.FloatField(tags={
        'title': ds_fields.TagReference('serial_number', gettext_noop("SFP Temperature (%(serial_number)s)")),
        'unit': 'C',
        'visualization': {
            'type': 'line',
            'initial_set': True,
            'time_downsamplers': ['mean'],
            'value_downsamplers': ['min', 'mean', 'max'],
        }
    })
    vcc = ds_fields.FloatField(tags={
        'title': ds_fields.TagReference('serial_number', gettext_noop("SFP VCC (%(serial_number)s)")),
        'unit': 'V',
        'visualization': {
            'type': 'line',
            'initial_set': True,
            'time_downsamplers': ['mean'],
            'value_downsamplers': ['min', 'mean', 'max'],
        }
    })
    tx_bias = ds_fields.FloatField(tags={
        'title': ds_fields.TagReference('serial_number', gettext_noop("SFP TX Bias (%(serial_number)s)")),
        'unit': 'mW',
        'visualization': {
            'type': 'line',
            'initial_set': True,
            'time_downsamplers': ['mean'],
            'value_downsamplers': ['min', 'mean', 'max'],
        }
    })
    tx_power = ds_fields.FloatField(tags={
        'title': ds_fields.TagReference('serial_number', gettext_noop("SFP TX Power (%(serial_number)s)")),
        'unit': 'mW',
        'visualization': {
            'type': 'line',
            'initial_set': True,
            'time_downsamplers': ['mean'],
            'value_downsamplers': ['min', 'mean', 'max'],
        }
    })
    rx_power = ds_fields.FloatField(tags={
        'title': ds_fields.TagReference('serial_number', gettext_noop("SFP RX Power (%(serial_number)s)")),
        'unit': 'mW',
        'visualization': {
            'type': 'line',
            'initial_set': True,
            'time_downsamplers': ['mean'],
            'value_downsamplers': ['min', 'mean', 'max'],
        }
    })

    def get_stream_query_tags(self):
        """
        Returns a set of tags that uniquely identify this object.

        :return: A dictionary of tags that uniquely identify this object
        """

        tags = super(SFPMonitorStreams, self).get_stream_query_tags()
        tags.update({'serial_number': self._model.serial_number})
        return tags

    def get_stream_tags(self):
        """
        Returns the stream tags that should be included in every stream
        derived from this object.

        :return: A dictionary of tags to include
        """

        tags = super(SFPMonitorStreams, self).get_stream_tags()
        tags.update({'serial_number': self._model.serial_number})
        return tags

ds_pool.register(SFPMonitor, SFPMonitorStreams)

# In case we have the frontend module installed, we also subscribe to its
# reset signal that gets called when a user requests a node's data to be reset.
try:
    from nodewatcher.modules.frontend.editor import signals as editor_signals

    @dispatch.receiver(editor_signals.reset_node)
    def sensors_node_reset(sender, request, node, **kwargs):
        """
        Remove all SFP data when a user requests the node to be reset.
        """

        node.monitoring.irnas.sfp(queryset=True).delete()
except ImportError:
    pass
