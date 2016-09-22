from kuryr_kubernetes.context import base
from kuryr_kubernetes.context import objects as ctx_obj


class AnnotationsProvider(base.StateProvider):
    def __init__(self, kubernetes_client):
        self._client = kubernetes_client

    def ensure_absent(self, annotations):
        pass

    def ensure_present(self, annotations):
        data = self._client.annotate(annotations.link, annotations)
        return ctx_obj.Annotations(annotations.link, data)
