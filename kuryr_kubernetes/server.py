# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import eventlet

eventlet.monkey_patch()

import sys

from oslo_log import log as logging
from oslo_service import service
from neutronclient.neutron import client as neutron_client

from kuryr_kubernetes import config

from kuryr_kubernetes import events
from kuryr_kubernetes.context import objects
from kuryr_kubernetes import k8s_client
from kuryr_kubernetes.context import base as ctx_base
from kuryr_kubernetes.context import watch_providers as ctx_watch
from kuryr_kubernetes.context.controller_providers import port as ctx_port
from kuryr_kubernetes.context.controller_providers import \
    annotations as ctx_anno
from kuryr_kubernetes.processors import base as proc_base
from kuryr_kubernetes.processors import async as proc_async
from kuryr_kubernetes.processors.controller import pod as proc_pod

LOG = logging.getLogger(__name__)


class KuryrK8sService(service.Service):
    def __init__(self):
        super(KuryrK8sService, self).__init__()
        kubernetes = k8s_client.K8sClient("http://192.168.20.243:8080")
        neutron = neutron_client.Client(
            '2.0',
            username='admin',
            tenant_name='admin',
            password='secret',
            auth_url='http://192.168.20.243:5000/v2.0',
        )

        context = ctx_base.Context()
        processors = proc_base.EventProcessors()
        watcher = ctx_watch.AsyncWatchProvider(kubernetes, processors, self.tg)

        processors.register(events.K8sEvent, proc_async.AsyncProcessor(
            proc_base.NOOPProcessor(), self.tg))
        processors.register(events.PodEvent,
                            proc_async.AsyncProcessor(proc_pod.PodProcessor(
                                context), self.tg, events.K8sEvent.object_uid))

        context.add_provider(objects.Watch, watcher)
        context.add_provider(objects.Port, ctx_port.PortProvider(neutron))
        context.add_provider(objects.Annotations,
                             ctx_anno.AnnotationsProvider(kubernetes))

        context.ensure_present(
            objects.Watch("/api/v1/namespaces", events.NamespaceEvent))
        context.ensure_present(
            objects.Watch("/api/v1/namespaces/default/pods", events.PodEvent))

        context.put(objects.NamespaceNetwork(
            namespace='default',
            neutron_network={u'provider:physical_network': None,
                             u'ipv6_address_scope': None,
                             u'port_security_enabled': True,
                             u'provider:network_type': u'vxlan',
                             u'id': u'9c05aa96-7299-4c34-8e0a-6780eb586318',
                             u'router:external': True,
                             u'availability_zone_hints': [],
                             u'availability_zones': [u'nova'],
                             u'ipv4_address_scope': None, u'shared': False,
                             u'status': u'ACTIVE', u'subnets': [
                    u'6efc5721-debe-45bd-b146-258bab88377b',
                    u'454c6f66-ee67-4680-a743-3214475dec70'],
                             u'description': u'', u'tags': [],
                             u'updated_at': u'2016-09-21T19:15:40',
                             u'is_default': True,
                             u'provider:segmentation_id': 1089,
                             u'name': u'public', u'admin_state_up': True,
                             u'tenant_id': u'8b61b8cc856f4387bcd5d1f5e5ee7971',
                             u'created_at': u'2016-09-21T19:15:40',
                             u'mtu': 1450},
            neutron_subnet={u'description': u'', u'enable_dhcp': False,
                            u'network_id': u'9c05aa96-7299-4c34-8e0a-6780eb586318',
                            u'tenant_id': u'8b61b8cc856f4387bcd5d1f5e5ee7971',
                            u'created_at': u'2016-09-21T19:15:42',
                            u'dns_nameservers': [],
                            u'updated_at': u'2016-09-21T19:15:42',
                            u'ipv6_ra_mode': None, u'allocation_pools': [
                    {u'start': u'172.24.4.2', u'end': u'172.24.4.254'}],
                            u'gateway_ip': u'172.24.4.1',
                            u'ipv6_address_mode': None, u'ip_version': 4,
                            u'host_routes': [], u'cidr': u'172.24.4.0/24',
                            u'id': u'454c6f66-ee67-4680-a743-3214475dec70',
                            u'subnetpool_id': None, u'name': u'public-subnet'},
        ))

        self.watcher = watcher

    def start(self):
        self.watcher.start()

    def wait(self):
        """Waits for K8sController to complete."""
        super(KuryrK8sService, self).wait()

    def stop(self, graceful=False):
        """Stops the event loop if it's not stopped already."""
        self.watcher.stop()
        super(KuryrK8sService, self).stop(graceful)


def start():
    config.init(sys.argv[1:])
    config.setup_logging()
    kuryrk8s_launcher = service.launch(config.CONF, KuryrK8sService())
    kuryrk8s_launcher.wait()


if __name__ == '__main__':
    start()
