from eventlet import queue as eventlet_queue
from oslo_log import log as logging

from kuryr_kubernetes.processors import base


LOG = logging.getLogger(__name__)

QUEUE_SIZE = 100
GRACE_TIMEOUT = 5


class AsyncProcessor(base.EventProcessor):
    def __init__(self, delegate, thread_group, group_by=None):
        self._delegate = delegate
        self._tg = thread_group
        self._group_by = group_by
        self._queues = {}

    def process(self, event):
        if self._group_by is None:
            self._tg.add_thread(self._delegate, event)
            return

        group = self._group_by(event)
        queue = self._queues.get(group)
        if queue is None:
            queue = eventlet_queue.LightQueue(maxsize=QUEUE_SIZE)
            self._queues[group] = queue
            self._tg.add_thread(self._processing_loop, group, queue)
        queue.put(event)

    def _processing_loop(self, group, queue):
        LOG.debug("%r started processing group %s" % (self, group))
        try:
            while True:
                LOG.debug("%r has %s processors pending for group %s" % (
                    self, queue.qsize(), group))
                try:
                    event = queue.get(timeout=GRACE_TIMEOUT)
                    self._delegate(event)
                except eventlet_queue.Empty:
                    return
        finally:
            del self._queues[group]
            LOG.debug("%r finished processing group %s" % (self, group))

    def __repr__(self):
        return "%s:%r" % (super(AsyncProcessor, self).__repr__(),
                          self._delegate)
