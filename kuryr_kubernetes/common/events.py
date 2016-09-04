import abc

import six
from oslo_service import loopingcall

# FIXME: add timeouts and proper exception list
neutron_retry = loopingcall.RetryDecorator(exceptions=(Exception,))


class Broadcast(object):
    def __init__(self, *callbacks):
        self.callbacks

    def __call__(self, event):
        for callback in self.callbacks:
            callback(event)


class Filter(object):
    def __init__(self, predicate, callback):
        self.predicate = predicate
        self.callback = callback

    def __call__(self, event):
        if self.predicate(event):
            self.callback(event)


class Dispatch(object):
    def __init__(self, dispatcher, callback):
        self.dispatcher = dispatcher
        self.callback = callback

    def __call__(self, event):
        self.dispatcher(self.callback, event)


@six.add_metaclass(abc.ABCMeta)
class EventHandler(object):
    @abc.abstractmethod
    def match_event(self, event):
        pass

    @abc.abstractmethod
    def process_event(self, event):
        pass
