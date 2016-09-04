import abc
import six


class K8sCNIRequest(object):
    def __init__(self, env):
        cni_args = dict(
            tuple(i.strip() for i in arg.split("=", 1))
            for arg in env['CNI_ARGS'].split(";")
        )
        self.command = env['CNI_COMMAND']
        self.ifname = env['CNI_IFNAME']
        self.netns = env['CNI_NETNS']
        self.pod_namespace = cni_args['K8S_POD_NAMESPACE']
        self.pod_name = cni_args['K8S_POD_NAME']
        self.pod_container_id = cni_args['K8S_POD_INFRA_CONTAINER_ID']


class K8sCNIResponse(object):
    pass


class K8sCNIError(K8sCNIResponse):
    pass


class K8sCNIPlugin(object):
    def __init__(self, driver):
        self._command_handlers = {
            'ADD': driver.add,
            'DEL': driver.delete,
            'VERSION': self.version,
        }

    def run(self, env):
        request = K8sCNIRequest(env)
        handler = self._command_handlers.get(request.command)
        if handler:
            response = handler(request)
        else:
            raise K8sCNIError()
        return 0

    def version(self):
        return K8sCNIResponse()


@six.add_metaclass(abc.ABCMeta)
class K8sCNIDriver(object):
    @abc.abstractmethod
    def add(self, request):
        pass

    @abc.abstractmethod
    def delete(self, request):
        pass
