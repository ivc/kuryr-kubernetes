ADDED = 'ADDED'
MODIFIED = 'MODIFIED'
DELETED = 'DELETED'


class K8sEvent(dict):
    def object_uid(self):
        return self['object']['metadata']['uid']

    def object_kind(self):
        return self['object']['kind']

    def event_type(self):
        return self['type']

    def __str__(self):
        return "%s(id=%s, type=%s, object_kind=%s, object_uid=%s)" % (
            type(self).__name__, id(self),
            self.event_type(), self.object_kind(), self.object_uid()
        )

    def __repr__(self):
        return "%s(%s)" % (type(self).__name__,
                           super(K8sEvent, self).__repr__())


class NamespaceEvent(K8sEvent):
    pass


class PodEvent(K8sEvent):
    pass


class ServiceEvent(K8sEvent):
    pass


class EndpointsEvent(K8sEvent):
    pass