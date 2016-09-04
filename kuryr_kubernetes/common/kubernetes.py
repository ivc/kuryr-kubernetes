import json
import requests

from kuryr_kubernetes.common import constants as const


class Client(object):
    # TODO: exceptions, cleanup
    # also check openstack/python-k8sclient (does not support watch api atm)
    def __init__(self, url):
        self.url = url

    def get(self, kind, **key):
        url = self.url + kind.format_link(**key)
        data = requests.get(url).json()
        return kind.from_dict(data)

    def annotate(self, obj, annotations):
        url = self.url + obj.metadata.selfLink
        data = json.dumps({
            "kind": obj.kind,
            "apiVersion": "v1",
            "metadata": {
                "annotations": {
                    k: v if isinstance(v, str) else json.dumps(v)
                    for k, v in annotations.items()
                }
            }
        })
        requests.patch(url, data=data, headers={
            'Content-Type': 'application/merge-patch+json',
            'Accept': 'application/json',
        })

    def watch(self, obj, callback):
        params = {'watch': 'true'}
        # FIXME: do not use Pod without a name
        if not obj.metadata.name:
            url = self.url + obj.metadata.selfLink
        else:
            url = self.url + obj.format_link(namespace=obj.metadata.namespace)
        print(url)
        print(params)
        response = requests.get(url, params=params, stream=True)
        for line in response.iter_lines(delimiter='\n'):
            if line.strip():
                event = json.loads(line)
                callback(Event(event['type'],
                         type(obj).from_dict(event['object'])))

class Event(object):
    def __init__(self, event, obj):
        self.added = event == 'ADDED'
        self.modified = event == 'MODIFIED'
        self.deleted = event == 'DELETED'
        self.obj = obj


class ObjectMetadata(object):
    @classmethod
    def from_dict(cls, data):
        obj = cls()
        obj.annotations = {
            k: (json.loads(v) if k.startswith(const.ANNOTATION_PREFIX) else v)
            for k, v in data.pop('annotations', {}).items()
        }
        vars(obj).update(data)
        return obj

    def __str__(self):
        return str({k: str(v) for k, v in vars(self).items()})


class PodSpec(object):
    @classmethod
    def from_dict(cls, data):
        obj = cls()
        vars(obj).update(data)
        return obj

    def __str__(self):
        return str({k: str(v) for k, v in vars(self).items()})


class Pod(object):
    format_link = "/api/v1/namespaces/{namespace}/pods/{name}".format

    def __init__(self, **key):
        # FIXME: this is ugly
        if key:
            if 'name' not in key:
                key['name'] = ''
            self.metadata = ObjectMetadata()
            self.metadata.name = key['name']
            self.metadata.namespace = key['namespace']
            self.metadata.selfLink = self.format_link(**key)
            self.kind = "Pod"

    @classmethod
    def from_dict(cls, data):
        obj = cls()
        obj.metadata = ObjectMetadata.from_dict(data.pop('metadata'))
        obj.spec = PodSpec.from_dict(data.pop('spec'))
        vars(obj).update(data)
        return obj

    def __str__(self):
        return str({k: str(v) for k, v in vars(self).items()})
