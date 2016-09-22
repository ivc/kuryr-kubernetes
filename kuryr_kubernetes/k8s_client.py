import contextlib
import json
import requests


class K8sClientException(Exception):
    pass


class K8sClient(object):
    # TODO: exceptions, multiple base_url

    def __init__(self, base_url):
        self._base_url = base_url

    def get(self, path):
        url = self._base_url + path
        response = requests.get(url)
        if not response.ok:
            raise K8sClientException(response.text)
        return response.json()

    def annotate(self, path, annotations):
        url = self._base_url + path
        data = json.dumps({
            "metadata": {
                "annotations": annotations
            }
        })
        response = requests.patch(url, data=data, headers={
            'Content-Type': 'application/merge-patch+json',
            'Accept': 'application/json',
        })
        if not response.ok:
            raise K8sClientException(response.text)
        return response.json()['metadata']['annotations']

    def watch(self, path):
        params = {'watch': 'true'}
        url = self._base_url + path

        # TODO: connection refused exception
        with contextlib.closing(requests.get(url, params=params,
                                             stream=True)) as response:
            if not response.ok:
                raise K8sClientException(response.text)
            for line in response.iter_lines(delimiter='\n'):
                line = line.strip()
                if line:
                    yield json.loads(line)
