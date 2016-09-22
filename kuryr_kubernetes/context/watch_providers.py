import time

from oslo_log import log as logging

from kuryr_kubernetes.context import base
from kuryr_kubernetes import k8s_client


LOG = logging.getLogger(__name__)


class WatchProvider(base.StateProvider):
    def __init__(self, kubernetes_client, event_processor):
        self._client = kubernetes_client
        self._processor = event_processor
        self._active = {}
        self._registered = {}
        self._running = False

    def ensure_present(self, watch):
        key = watch.get_key()
        registered = self._registered.setdefault(key, watch)

        if self._running and not self._active.get(key):
            self._active[key] = True
            self._run(registered)

        return registered

    def ensure_absent(self, watch):
        key = watch.get_key()
        self._active.pop(key, None)
        return self._registered.pop(key, watch)

    def _run(self, watch):
        # TODO: exceptions
        key = watch.get_key()
        try:
            while self._running and self._active.get(key):
                try:
                    for event in self._client.watch(watch.path):
                        self._processor(watch.event_type(event))
                        if not (self._running and self._active.get(key)):
                            break
                except k8s_client.K8sClientException as ex:
                    LOG.error(str(ex))
                    time.sleep(10)
        finally:
            self._active.pop(key, None)

    def start(self):
        self._running = True
        for watch in self._registered.values():
            self.ensure_present(watch)

    def stop(self):
        self._running = False


class AsyncWatchProvider(WatchProvider):
    def __init__(self, kubernetes_client, event_processor, thread_group):
        super(AsyncWatchProvider, self).__init__(kubernetes_client, event_processor)
        self._tg = thread_group

    def _run(self, watch):
        self._tg.add_thread(super(AsyncWatchProvider, self)._run, watch)
