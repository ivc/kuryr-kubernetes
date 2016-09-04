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

# FIXME: move this to the cmd launcher
import kuryr_kubernetes.server.handlers

eventlet.monkey_patch(socket=True)

import sys

from oslo_log import log as logging
from oslo_service import service
from oslo_service import loopingcall

from kuryr.lib import utils
from kuryr_kubernetes import config
from kuryr_kubernetes.common import kubernetes as k8s
from kuryr_kubernetes.common import events as ev
from kuryr_kubernetes.server import handlers

LOG = logging.getLogger(__name__)

# FIXME: proper exception list
restarting = loopingcall.RetryDecorator(exceptions=(Exception,))


class KuryrK8sService(service.Service):

    def __init__(self, conf):
        super(KuryrK8sService, self).__init__()
        self.conf = conf

    def start(self):
        # TODO: prolly need 2 pools - 1 for namespaces to spawn pod/service
        # watchers and the other for the pods/services themselves
        self.pool = eventlet.GreenPool()
        self.k8s_client = k8s.Client(self.conf.kubernetes.api_root)
        self.neutron_client = utils.get_neutron_client_simple(
            url=self.conf.neutron_client.neutron_uri,
            auth_url=self.conf.keystone_client.auth_uri,
            token=self.conf.keystone_client.admin_token,
        )
        self.pool.spawn_n(self.watch_pods)

    def wait(self):
        """Waits for K8sController to complete."""
        super(KuryrK8sService, self).wait()
        self.pool.waitall()

    def stop(self, graceful=False):
        """Stops the event loop if it's not stopped already."""
        super(KuryrK8sService, self).stop(graceful)

    @restarting
    def watch_pods(self):
        clients = {'k8s_client': self.k8s_client,
                   'neutron_client': self.neutron_client}
        handler_list = [
            handlers.CreatePort(**clients),
            handlers.WaitForPortActivation(**clients),
        ]
        pipeline = ev.Broadcast(
            ev.Filter(hdl.match_event,
                      ev.Dispatch(self.pool.spawn_n, hdl.process_event))
            for hdl in handler_list
        )
        while True:
            # FIXME
            self.k8s_client.watch(k8s.Pod(namespace='default'), pipeline)


def start():
    config.init(sys.argv[1:])
    config.setup_logging()
    kuryrk8s_launcher = service.launch(config.CONF,
                                       KuryrK8sService(config.CONF))
    kuryrk8s_launcher.wait()


if __name__ == '__main__':
    start()
