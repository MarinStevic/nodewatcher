from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models
from django.utils.translation import ugettext_lazy as _

from nodewatcher.registry import fields as registry_fields
from nodewatcher.utils import ipaddr

class PoolAllocationError(Exception):
  pass

class IpPoolStatus:
  """
  Possible pools states.
  """
  Free = 0
  Full = 1
  Partial = 2

class PoolBase(models.Model):
  """
  An abstract base class for all pool implementations.
  """
  class Meta:
    abstract = True
  
  parent = models.ForeignKey('self', null = True, related_name = 'children')
  projects = models.ManyToManyField("nodes.Project", related_name = 'pools_%(app_label)s_%(class)s')
  
  # Bookkeeping for allocated pools
  allocation_content_type = models.ForeignKey(ContentType, null = True)
  allocation_object_id = models.CharField(max_length = 50, null = True)
  allocation_content_object = generic.GenericForeignKey('allocation_content_type', 'allocation_object_id')
  allocation_timestamp = models.DateTimeField(null = True)

  @classmethod
  def modifies_pool(cls, f):
    def decorator(self, *args, **kwargs):
      # Lock our own instance
      locked_instance = self.__class__.objects.select_for_update().get(pk = self.pk)
      return f(locked_instance, *args, **kwargs)

    return decorator

  def top_level(self):
    """
    Returns the root of this pool tree.
    """
    if self.parent:
      return self.parent.top_level()
    
    return self
  
  def free(self):
    """
    Frees this allocated item and returns it to the parent pool.
    """
    raise NotImplementedError

class IpPool(PoolBase):
  """
  This class represents an IP pool - that is a subnet available for
  allocation purpuses. Every IP block that is allocated is represented
  as an IpPool instance with proper parent pool reference.
  """
  family = registry_fields.SelectorKeyField("node.config", "core.interfaces.network#ip_family")
  network = models.CharField(max_length = 50)
  prefix_length = models.IntegerField()
  status = models.IntegerField(default = IpPoolStatus.Free)
  description = models.CharField(max_length = 200, null = True)
  prefix_length_default = models.IntegerField(null = True)
  prefix_length_minimum = models.IntegerField(default = 24, null = True)
  prefix_length_maximum = models.IntegerField(default = 28, null = True)
  ip_subnet = registry_fields.IPAddressField(null = True)
  
  class Meta:
    app_label = "core"
  
  def save(self, **kwargs):
    """
    Saves the model.
    """
    self.ip_subnet = '%s/%s' % (self.network, self.prefix_length)
    super(IpPool, self).save(**kwargs)
  
  def _split_buddy(self):
    """
    Splits this pool into two subpools.

    WARNING: This method must be called on an object that is locked for
    updates using `select_for_update`. Otherwise this will cause corruptions.
    """
    net = ipaddr.IPNetwork("%s/%d" % (self.network, self.prefix_length))
    net0, net1 = net.subnet()

    left = IpPool(parent = self, family = self.family, network = str(net0.network), prefix_length = net0.prefixlen)
    right = IpPool(parent = self, family = self.family, network = str(net1.network), prefix_length = net1.prefixlen)
    left.save()
    right.save()
    
    self.status = IpPoolStatus.Partial
    self.save()
    
    return left, right

  @PoolBase.modifies_pool
  def reserve_subnet(self, network, prefix_len, check_only = False):
    """
    Attempts to reserve a specific subnet in the allocation pool. The subnet
    must be a valid subnet and must be allocatable.
    
    @param network: Subnet address
    @param prefix_len: Subnet prefix length
    @param check_only: Should only a check be performed and no actual allocation
    """
    if prefix_len == 31:
      return None
    
    if not self.parent and (prefix_len < self.prefix_length_minimum or prefix_len > self.prefix_length_maximum):
      return None 

    if ipaddr.IPNetwork("%s/%d" % (network, prefix_len)) not in self.to_ip_network():
      # We don't contain this network, so there is nothing to be done
      return None
    
    if network == self.network and self.prefix_length == prefix_len and self.status == IpPoolStatus.Free:
      # We are the network, mark as full and save
      if not check_only:
        self.status = IpPoolStatus.Full
        self.save()
        return self
      else:
        return True
    
    # Find the proper network between our children
    alloc = None
    if self.children.count() > 0:
      for child in self.children.exclude(status = IpPoolStatus.Full).select_for_update():
        alloc = child.reserve_subnet(network, prefix_len, check_only)
        if alloc:
          break
      else:
        return None
      
      # Something has been allocated, update our status
      if self.children.filter(status = IpPoolStatus.Full).count() == 2 and not check_only:
        self.status = IpPoolStatus.Full
        self.save()
    else:
      # Split ourselves into two halves
      for child in self._split_buddy():
        alloc = child.reserve_subnet(network, prefix_len, check_only)
        if alloc:
          break
      
      if not alloc or check_only:
        # Nothing has been allocated, this means that the given subnet
        # was invalid. Remove all children and become free again.
        self.children.all().delete()
        self.status = IpPoolStatus.Free
        self.save()
    
    return alloc

  def _allocate_buddy(self, prefix_len):
    """
    Allocate IP addresses from the pool in a buddy-like allocation scheme. This
    operation may split existing free pools into smaller ones to accomodate the
    new allocation.

    WARNING: This method must be called on an object that is locked for
    updates using `select_for_update`. Otherwise this will cause corruptions.
    
    @param prefix_len: Wanted prefix length
    """
    if self.prefix_length > prefix_len:
      # We have gone too far, allocation has failed
      return None
    
    if prefix_len == self.prefix_length and self.status == IpPoolStatus.Free:
      # We have found a free pool of the proper size, use it
      self.status = IpPoolStatus.Full
      self.save()
      return self
    
    # Pool not found, check if we have children - if we don't we'll have to split
    # and traverse the left one
    alloc = None
    if self.children.count() > 0:
      for child in self.children.exclude(status = IpPoolStatus.Full).order_by("ip_subnet").select_for_update():
        alloc = child._allocate_buddy(prefix_len)
        if alloc:
          break
      else:
        return None
      
      # Something has been allocated, update our status
      if self.children.filter(status = IpPoolStatus.Full).count() == 2:
        self.status = IpPoolStatus.Full
        self.save()
    else:
      # Split ourselves into two halves and traverse the left half
      left, right = self._split_buddy()
      alloc = left._allocate_buddy(prefix_len)
    
    return alloc

  @PoolBase.modifies_pool
  def reclaim_pools(self):
    """
    Coalesces free children back into one if possible.
    """
    if self.status == IpPoolStatus.Free:
      return self.parent.reclaim_pools() if self.parent else None
    
    # When all children are free, we don't need them anymore; when only some
    # are free, we mark this pool as partially free
    free_children = self.children.filter(status = IpPoolStatus.Free).count()
    if  free_children == 2:
      self.children.all().delete()
      self.status = IpPoolStatus.Free
      self.save()
      return self.parent.reclaim_pools() if self.parent else None
    elif free_children == 1:
      self.status = IpPoolStatus.Partial
      self.save()
      return self.parent.reclaim_pools() if self.parent else None
    else:
      # If any of the children are partial, we are partial as well
      if self.children.filter(status = IpPoolStatus.Partial).count() > 0:
        self.status = IpPoolStatus.Partial
        self.save()
        return self.parent.reclaim_pools() if self.parent else None

  @PoolBase.modifies_pool
  def free(self):
    """
    Frees this allocated item and returns it to the parent pool.
    """
    self.status = IpPoolStatus.Free
    self.allocation_content_object = None
    self.allocation_timestamp = None
    self.save()
    self.reclaim_pools()
  
  def is_leaf(self):
    """
    Returns true if this pool has no children.
    """
    return self.children.all().count() == 0

  def family_as_string(self):
    """
    Returns this pool's address family as a string.
    """
    for enum, desc in self._meta.get_field_by_name("family")[0].choices:
      if enum == self.family:
        return desc
    
    return _("unknown")

  def __unicode__(self):
    """
    Returns a string representation of this pool.
    """
    if self.description:
      return u"%s [%s/%d]" % (self.description, self.network, self.prefix_length)
    else: 
      return u"%s/%d" % (self.network, self.prefix_length)
  
  def to_ip_network(self):
    """
    Returns the allocation as an ipaddr.IPNetwork instance.
    """
    return ipaddr.IPNetwork("%s/%d" % (self.network, self.prefix_length))

  @PoolBase.modifies_pool
  def allocate_subnet(self, prefix_len = None):
    """
    Attempts to allocate a subnet from this pool.

    @param prefix_len: Wanted prefix length
    @return: A valid IpPool instance of the allocated subpool
    """
    if not prefix_len:
      prefix_len = self.prefix_length_default
    
    if prefix_len < self.prefix_length_minimum or prefix_len > self.prefix_length_maximum:
      return None
    
    if prefix_len == 31:
      return None

    pool = self._allocate_buddy(prefix_len)
    return pool
