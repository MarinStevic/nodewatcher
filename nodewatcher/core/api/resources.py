from django.contrib.gis.db import models as gis_models
from django.db.models import query
from django.utils import six

from tastypie import fields as tastypie_fields, resources
from tastypie.contrib.gis import resources as gis_resources

from django_datastream import resources as datastream_resources, serializers

import jsonfield

from ..registry import fields as registry_fields
from nodewatcher.utils import trimming

from . import fields, paginator

# Exports
__all__ = [
    'BaseResource',
]


class AllFiltering(object):
    # Special class which makes Tastypie allow filtering on all
    # fields, including all related fields, of a given resource.

    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return resources.ALL_WITH_RELATIONS


class BaseMetaclass(resources.ModelDeclarativeMetaclass):
    def __new__(cls, name, bases, attrs):
        # Override Meta defaults
        if attrs.get('Meta') and not getattr(attrs['Meta'], 'serializer', None):
            attrs['Meta'].serializer = serializers.DatastreamSerializer()
        if attrs.get('Meta') and not getattr(attrs['Meta'], 'paginator_class', None):
            attrs['Meta'].paginator_class = paginator.Paginator

        new_class = super(BaseMetaclass, cls).__new__(cls, name, bases, attrs)

        # We override use_in function on all fields to be able to limit the fields user
        # wants in the output.
        for name, field in new_class.base_fields.items():
            # These are provided by Tastypie and we want to show them always if they are enabled through resource options.
            if name in ['resource_uri', 'absolute_url']:
                continue
            field.use_in = new_class.field_use_in_factory(name, getattr(field, 'use_in', None))

        return new_class


class BaseResource(six.with_metaclass(BaseMetaclass, resources.NamespacedModelResource, gis_resources.ModelResource, datastream_resources.BaseResource)):
    # In class methods which are called from a metaclass we cannot use super() because BaseResource is not
    # yet defined then. We cannot call gis_resources.ModelResource.<method>() either, because then our current
    # cls is not given, but gis_resources.ModelResource is used instead. So we create a custom function where skip
    # the @classmethod decorator and access underlying unbound function stored in im_func instead. We have to use
    # gis_resources.ModelResource branch of inheritance because it does not do it by itself, but it is OK, because
    # we do not really care about namespaces when called from a metaclass.

    @classmethod
    def should_skip_field(cls, field):
        def parent_should_skip_field():
            return gis_resources.ModelResource.should_skip_field.im_func(cls, field)

        # Skip fields created by the registry queryset internally for sorting purposes.
        if field.name.startswith('_'):
            return True

        if field.name in ('registry_metadata', 'annotations', 'display_order'):
            return True

        if isinstance(field, (registry_fields.RegistryRelationField, registry_fields.RegistryMultipleRelationField)):
            return False

        return parent_should_skip_field()

    @classmethod
    def api_field_from_django_field(cls, field, default=tastypie_fields.CharField):
        def parent_api_field_from_django_field():
            return gis_resources.ModelResource.api_field_from_django_field.im_func(cls, field, default)

        if isinstance(field, (registry_fields.RegistryRelationField, registry_fields.RegistryMultipleRelationField)):
            model2resource = {
                registry_fields.RegistryRelationField: fields.RegistryRelationField,
                registry_fields.RegistryMultipleRelationField: fields.RegistryMultipleRelationField,
            }

            def create_field(**kwargs):
                # TODO: Make this work for polymorphic models.
                class Resource(BaseResource):
                    class Meta:
                        object_class = field.rel.to
                        resource_name = '%s.%s' % (field.rel.to.__module__, field.rel.to.__name__)
                        list_allowed_methods = ('get',)
                        detail_allowed_methods = ('get',)
                        serializer = serializers.DatastreamSerializer()
                        excludes = ['id']
                        include_resource_uri = False
                        filtering = AllFiltering()

                f = model2resource[field.__class__](Resource, **kwargs)
                f.model_field = field
                return f

            return create_field
        else:
            if isinstance(field, jsonfield.JSONField):
                # TODO: Optimize this so that double conversion is not performed and that we pass raw JSON.
                field_class = tastypie_fields.DictField
            elif isinstance(field, gis_models.GeometryField):
                # Override with our GeometryField that knows how to extract GeoJSON from
                # the queryset in order to avoid slow GDAL conversions.
                field_class = fields.GeometryField
            else:
                field_class = parent_api_field_from_django_field()

            def create_field(**kwargs):
                f = field_class(**kwargs)
                f.model_field = field
                return f

            return create_field

    @classmethod
    def field_use_in_factory(cls, field_name, field_use_in):
        def select_field_use_in(bundle):
            if callable(field_use_in) and not field_use_in(bundle):
                return False

            only_fields = cls.value_to_list(getattr(bundle.request, 'GET', {}), 'fields')
            if not only_fields:
                return True

            # In ToOneField.dehydrate and ManyToManyField.dehydrate we are storing the path
            # as we are walking related fields so that we can have full path available here.
            # bundle.request is the only state available through all dehydration process so
            # we are using it. This currently works only on our fields, but can be ported to
            # other related fields by augmenting their dehydrate method.
            field_path = getattr(bundle.request, '_field_in_use_path', [])

            current_path = field_path + [field_name]

            # We select the field (return True) if current_path is a prefix to only_field.
            # If the last bit is empty (field selection ends with "__", like "foobar__")
            # and current_path is below the rest of only_field, then we select it as well.
            # This makes possible to allow all subfields of a given field, without
            # having to list them all. In the above example, "foobar" and all fields
            # below "foobar" would be allowed. This also means that "__" selection
            # string allow all fields of a resource (same as if field selection would
            # not be specified at all). This is different to the empty field selection
            # ("") which does not match any field and does not select any field at all.
            # In addition, we allow also "__foobar", which is the same as "foobar".

            for only_field in only_fields:
                if not only_field:
                    # Empty selection does not match any field. But let's check if there
                    # is some other which do match. (It is a bit pointless then to list
                    # an empty only_field as well, but, let's be generous about the input.
                    continue

                # Remove any trailing "__" (both "__foobar" and "foobar" are the same).
                # This makes "__" become an empty string, but we took care of that as
                # as special case above, so an empty string from here on matches everything
                # (while above matches nothing).
                if only_field.startswith('__'):
                    only_field = only_field[2:]

                # If field selector is empty, bits will be [''].
                bits = only_field.split('__')

                for i, path_segment in enumerate(current_path):
                    if i >= len(bits):
                        # We got to the end of bits and haven't yet returned
                        # True, so this only_field does not seem right. Let's
                        # try the next one.
                        break
                    elif path_segment == bits[i]:
                        if i == len(current_path) - 1:
                            # All bits until now matched and we are at the end
                            # of the current_path, return True.
                            return True
                        else:
                            # Otherwise let's continue with the next bit.
                            continue
                    elif bits[i] == '':
                        # The current bit is a wildcard bit. All subfields from
                        # here one match. We return True.
                        return True
                    else:
                        # This only_field does not seem right. Let's try the next one.
                        break

            return False

        return select_field_use_in

    @classmethod
    def get_fields(cls, fields=None, excludes=None):
        # Registry stores additional fields in as virtual fields and we reuse Tastypie
        # code to parse them by temporary assigning them to local fields

        def parent_get_fields():
            return gis_resources.ModelResource.get_fields.im_func(cls, fields, excludes)

        final_fields = parent_get_fields()

        if not cls._meta.object_class:
            return final_fields

        meta_fields = cls._meta.object_class._meta.local_fields
        try:
            cls._meta.object_class._meta.local_fields = cls._meta.object_class._meta.virtual_fields
            if hasattr(cls._meta.object_class._meta, 'fields'):
                del cls._meta.object_class._meta.fields
            cls._meta.object_class._meta._expire_cache()
            final_fields.update(parent_get_fields())
        finally:
            cls._meta.object_class._meta.local_fields = meta_fields
            if hasattr(cls._meta.object_class._meta, 'fields'):
                del cls._meta.object_class._meta.fields
            cls._meta.object_class._meta._expire_cache()

        return final_fields

    def build_schema(self):
        data = super(BaseResource, self).build_schema()

        for field_name, field_object in self.fields.items():
            # We process ListField specially here (and not use field's
            # build_schema) so that Tastypie's ListField can be used
            if isinstance(field_object, tastypie_fields.ListField):
                if getattr(field_object, 'field', None):
                    data['fields'][field_name]['content'] = {}

                    field_type = field_object.field.__class__.__name__.lower()
                    if field_type.endswith('field'):
                        field_type = field_type[:-5]
                    data['fields'][field_name]['content']['type'] = field_type

                    if field_object.field.__doc__:
                        data['fields'][field_name]['content']['help_text'] = trimming.trim(field_object.field.__doc__)

            if hasattr(field_object, 'build_schema'):
                data['fields'][field_name].update(field_object.build_schema())

            if getattr(field_object, 'model_field', None):
                if getattr(field_object.model_field, 'choices'):
                    choices = field_object.model_field.choices

                    try:
                        # Try to get only keys
                        choices = zip(*choices)[0]
                    except (KeyError, IndexError):
                        # If not possible, leave it as it is
                        pass

                    data['fields'][field_name].update({
                        'choices': choices,
                    })

        return data

    # A hook so that queryset can be further sorted after basic sorting has been
    # applied. This allows us to assure that there is always a defined order for
    # all objects even if basic sorting does not sort all objects (for example,
    # because key to sort on is the same for multiple objects). This is necessary
    # for pagination to work correctly, because SKIP and LIMIT works well for
    # pagination only when all objects have a defined order.
    def _after_apply_sorting(self, obj_list, options, order_by_args):
        return obj_list

    def apply_sorting(self, obj_list, options=None):
        # Makes sure sorting does not loose count of all objects before filtering.
        nonfiltered_count = obj_list._nonfiltered_count

        # To be able to assign the args below, we have to access the
        # variable as a reference, otherwise a new local variable is
        # created inside a function scope. So we create a dummy dict
        # which wraps the real value. This can be done better in Python 3.
        stored_order_by = {
            'value': []
        }

        # We temporary replace order_by method on the queryset to hijack
        # the arguments passed to the order_by so that we can pass them
        # to _after_apply_sorting.
        obj_list_order_by = obj_list.order_by

        def order_by(*args):
            stored_order_by['value'] = args
            return obj_list_order_by(*args)

        obj_list.order_by = order_by

        try:
            sorted_queryset = super(BaseResource, self).apply_sorting(obj_list, options)
        finally:
            # Restore the original order_by method. Just to be sure
            # if it is reused somewhere else as well.
            obj_list.order_by = obj_list_order_by

        sorted_queryset = self._after_apply_sorting(sorted_queryset, options, stored_order_by['value'])

        # Restore the count of all objects.
        sorted_queryset._nonfiltered_count = nonfiltered_count

        return sorted_queryset

    def authorized_read_list(self, object_list, bundle):
        # Since authorization filter is applied after the generic filters have been
        # applied, we need to account for the difference that the auth filter causes
        nonfiltered_count = object_list._nonfiltered_count
        count = object_list.count()
        filtered_queryset = super(BaseResource, self).authorized_read_list(object_list, bundle)
        delta = count - filtered_queryset.count()
        filtered_queryset._nonfiltered_count = nonfiltered_count - delta

        return filtered_queryset

    # A hook so that queryset can be modified before count for _nonfiltered_count is taken
    # (for filtering which should not be exposed through dataTables)
    def _before_apply_filters(self, request, queryset):
        return queryset

    def apply_filters(self, request, applicable_filters):
        queryset = self.get_object_list(request)
        queryset = self._before_apply_filters(request, queryset)
        filtered_queryset = queryset.filter(**applicable_filters)

        f = request.GET.get('filter', None)
        if f and getattr(self._meta, 'global_filter', None):
            if hasattr(filtered_queryset, 'registry_expand_proxy_field'):
                expand_proxy_field = filtered_queryset.registry_expand_proxy_field
            else:
                expand_proxy_field = lambda x: x
            # TODO: Q objects should transform registry field names automatically, so that we do not have to call registry_expand_proxy_field
            qs = [query.Q(**{expand_proxy_field('%s__icontains' % field): f}) for field in self._meta.global_filter]
            filter_query = qs[0]
            for q in qs[1:]:
                filter_query |= q
            filtered_queryset = filtered_queryset.filter(filter_query).distinct()

        # We store count of all objects before filtering to be able to provide it in paginator (used in dataTables)
        filtered_queryset._nonfiltered_count = queryset.count()

        return filtered_queryset

    def filter_value_to_python(self, value, field_name, filters, filter_expr, filter_type):
        if filter_type in ('in', 'range'):
            value = self.value_to_list(filters, filter_expr)
            value = [self.basic_filter_value_to_python(v) for v in value]

        else:
            value = self.basic_filter_value_to_python(value)

        return value
