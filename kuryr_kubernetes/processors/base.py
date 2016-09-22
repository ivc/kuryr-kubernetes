import abc
import inspect
import six

from kuryr.lib._i18n import _LE
from oslo_log import log as logging

from kuryr_kubernetes import events

LOG = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class EventProcessor(object):
    def __call__(self, event):
        LOG.debug("%r is processing %s = %r" % (self, event, event))
        try:
            self.process(event)
        except Exception as ex:
            LOG.error(_LE("%r failed to process %s: %s" % (self, event, ex)))

    @abc.abstractmethod
    def process(self, event):
        raise NotImplementedError()

    def __repr__(self):
        return "%s(id=%s)" % (type(self).__name__, id(self))


class EventProcessors(EventProcessor):
    def __init__(self):
        self._registry = {}

    def register(self, obj_type, processor):
        processors = self._registry.setdefault(obj_type, [])
        processors.append(processor)

    def process(self, event):
        mro = inspect.getmro(type(event))
        for event_type in mro:
            processors = self._registry.get(event_type, ())
            for processor in processors:
                processor(event)


class NOOPProcessor(EventProcessor):
    def process(self, event):
        pass


class K8sEventProcessor(EventProcessor):
    def __init__(self, context):
        self.context = context

    def process(self, event):
        event_type = event.event_type()
        if event_type == events.MODIFIED:
            self.on_modified(event)
            self.on_present(event)
        elif event_type == events.ADDED:
            self.on_added(event)
            self.on_present(event)
        elif event_type == events.DELETED:
            self.on_deleted(event)

    def on_added(self, event):
        pass

    def on_modified(self, event):
        pass

    def on_deleted(self, event):
        pass

    def on_present(self, event):
        pass
