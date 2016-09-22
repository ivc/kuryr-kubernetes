from oslo_log import log as logging

LOG = logging.getLogger(__name__)

class StateProvider(object):
    def ensure_present(self, obj):
        raise NotImplementedError()

    def ensure_absent(self, obj):
        raise NotImplementedError()


class Context(StateProvider):
    def __init__(self):
        self._registry = {}
        self._cache = {}

    def ensure_absent(self, obj):
        return self._registry[type(obj)].ensure_absent(obj)

    def ensure_present(self, obj):
        key = obj.get_key()
        cached = self._cache.get(key)
        if obj.is_compatible(cached):
            return cached
        LOG.debug("%r" % (obj))
        LOG.debug("%r" % (cached))
        self._cache[key] = self._registry[type(obj)].ensure_present(obj)
        return self._cache[key]

    def add_provider(self, obj_type, provider):
        if obj_type in self._registry:
            raise RuntimeError("Duplicate provider for %s" %
                               obj_type.__name__)
        self._registry[obj_type] = provider

    def get(self, obj):
        key = obj.get_key()
        cached = self._cache.get(key)
        if obj.is_compatible(cached):
            return cached
        return None

    def put(self, obj):
        key = obj.get_key()
        self._cache[key] = obj
        return obj
