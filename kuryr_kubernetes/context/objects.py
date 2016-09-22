import abc
import six

from kuryr_kubernetes import constants as const


@six.add_metaclass(abc.ABCMeta)
class ObjectBase(dict):
    @abc.abstractmethod
    def get_key(self):
        raise NotImplementedError()

    def is_compatible(self, obj):
        if type(self) != type(obj):
            return False
        if self.get_key() != obj.get_key():
            return False
        for k, v in self.items():
            if v != obj.get(k):
                return False
        return True

    def __str__(self):
        return "%s%s" % (type(self).__name__, self.get_key())


class Annotations(ObjectBase):
    def __init__(self, link, data):
        self.link = link
        data = {k: v for k, v in data.items()
                if k.startswith(const.ANNOTATION_PREFIX)}
        super(Annotations, self).__init__(data)

    def get_key(self):
        return self.link


class Watch(ObjectBase):
    def __init__(self, path, event_type):
        self.path = path
        self.event_type = event_type

    def get_key(self):
        return self.path


class Port(ObjectBase):
    def get_key(self):
        return self['network_id'], self['device_owner'], self['device_id']


class NamespaceNetwork(ObjectBase):
    def __init__(self, namespace, **kwargs):
        self.namespace = namespace
        super(NamespaceNetwork, self).__init__(kwargs)

    def get_key(self):
        return self.namespace
