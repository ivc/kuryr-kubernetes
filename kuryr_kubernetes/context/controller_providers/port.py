from kuryr_kubernetes.context import objects
from oslo_service import loopingcall

from kuryr_kubernetes import exceptions as k_exc
from kuryr_kubernetes.context import base


class PortProvider(base.StateProvider):
    _retry = loopingcall.RetryDecorator(
        inc_sleep_time=3, exceptions=(k_exc.IncompleteStateException,))

    def __init__(self, neutron_client):
        self._client = neutron_client

    @_retry
    def ensure_present(self, port):
        # TODO: docstring, logging

        ports = self._find_ports(port)

        if not ports:
            ports = [self._create_port(port)]

        candidate_port = ports[0]
        invalid_ports = ports[1:]

        if port.get('status') == 'ACTIVE':
            if not candidate_port.get('status') == 'ACTIVE':
                raise k_exc.IncompleteStateException()
            for invalid_port in invalid_ports:
                self._delete_port(invalid_port)

        return candidate_port

    def ensure_absent(self, port):
        # FIXME: stub
        raise NotImplementedError()

    def _find_ports(self, port):
        response = self._client.list_ports(device_owner=port['device_owner'],
                                           device_id=port['device_id'])
        found_ports = [objects.Port(p) for p in response.get('ports', [])]

        def rank(found_port):
            port_rank = 0
            if found_port['id'] == port.get('id'):
                port_rank += 1
            if found_port['status'] == 'ACTIVE':
                port_rank += 2
            return port_rank

        def sort_key(ranked_port):
            port_rank, found_port = ranked_port
            return port_rank, found_port['id']

        return [p for r, p in sorted(
            [(rank(p), p) for p in found_ports],
            key=sort_key, reverse=True)]

    def _create_port(self, port):
        request = {k: port[k] for k in (
            'device_id',
            'device_owner',
            'network_id',
            'name',
            'binding:host_id',
            'fixed_ips')}
        request.update({
            'admin_state_up': True,
        })
        response = self._client.create_port({'port': request})
        return objects.Port(response['port'])

    def _delete_port(self, port):
        if port.get('status') == 'ACTIVE':
            raise k_exc.InvalidStateException()
        self._client.delete_port(port['id'])
        return port
