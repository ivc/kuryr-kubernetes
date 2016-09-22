import json
from kuryr_kubernetes.context import objects as ctx_obj
from kuryr_kubernetes.processors import base
from kuryr_kubernetes import constants as const


class PodProcessor(base.K8sEventProcessor):
    def on_present(self, event):
        metadata = event['object']['metadata']
        spec = event['object']['spec']
        netinfo = self.context.ensure_present(ctx_obj.NamespaceNetwork(namespace=metadata['namespace']))
        net = netinfo['neutron_network']
        subnet = netinfo['neutron_subnet']
        port = self.context.ensure_present(ctx_obj.Port({
            'name': "Pod-%s-%s" % (metadata['namespace'], metadata['name']),
            'device_owner': 'compute:kuryr',
            'device_id': metadata['uid'],
            'binding:host_id': spec['nodeName'],
            'network_id': net['id'],
            'admin_state_up': True,
            'fixed_ips': [{'subnet_id': subnet['id']}]
        }))
        self.context.ensure_present(ctx_obj.Annotations(metadata['selfLink'], {
            const.PORT_ANNOTATION: json.dumps(port, sort_keys=True),
            const.SUBNET_ANNOTATION: json.dumps(subnet, sort_keys=True),
        }))
        port['status'] = 'ACTIVE'
        port = self.context.ensure_present(port)
        self.context.ensure_present(ctx_obj.Annotations(metadata['selfLink'], {
            const.PORT_ANNOTATION: json.dumps(port, sort_keys=True),
            const.SUBNET_ANNOTATION: json.dumps(subnet, sort_keys=True),
        }))

    def on_deleted(self, event):
        pass
