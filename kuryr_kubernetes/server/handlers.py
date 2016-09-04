from oslo_service import loopingcall

from kuryr_kubernetes.common import constants as const
from kuryr_kubernetes.common.events import EventHandler
from kuryr_kubernetes.common import kubernetes as k8s

# FIXME: move Retry to somewhere in common and add a message
class Retry(Exception):
    pass

# FIXME: add timeouts, maybe from conf
neutron_retry = loopingcall.RetryDecorator(exceptions=(Retry,))

class CreatePort(EventHandler):
    def match_event(self, event):
        if not event.added:
            return
        port = event.obj.metadata.annotations.get(const.PORT_ANNOTATION)
        return not port

    def process_event(self, event):
        pod = event.obj
        network = self.poll_network_annotation(pod.metadata.namespace)

    @neutron_retry
    def poll_network_annotation(self, namespace):
        # TODO: implement Namespace
        ns = self.k8s_client.get(k8s.Namespace, namespace=namespace)
        net = ns.metadata.annotations.get(const.NETWORK_ANNOTATION)
        if not net:
            raise Retry()
        return net


class WaitForPortActivation(EventHandler):
    def match_event(self, event):
        if event.deleted:
            return
        port = event.obj.metadata.annotations.get(const.PORT_ANNOTATION)
        if not port:
            return
        return port['status'] == 'DOWN'

    def process_event(self, event):
        port = event.obj.metadata.annotations.get(const.PORT_ANNOTATION)
        active_port = self.poll_neutron_port_activation(port['id'])
        self.k8s_client.annotate(event.obj,
                                 {const.PORT_ANNOTATION: active_port})

    @neutron_retry
    def poll_neutron_port(self, port_id):
        port = self.neutron_client.show_port(port_id)
        if port['status'] != 'UP':
            raise Retry()
        return port