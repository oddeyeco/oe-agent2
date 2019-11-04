import lib.record_rate
import lib.commonclient
import lib.getconfig
import lib.puylogger
import lib.basecheck
import re

metrics = lib.getconfig.getparam('kube-state-metrics', 'metrics')
podstats = lib.getconfig.getparam('kube-state-metrics', 'podinfo')
check_type = 'kube-state-metrics'
greps = ['kube_deployment_status_replicas', 'kube_endpoint_address_available']
pods = ('kube_pod_container_status_waiting{', 'kube_pod_container_resource_limits_memory_bytes', 'kube_pod_container_resource_limits_cpu_cores')

if podstats:
    for y in pods:
        greps.append(y)


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            data = lib.commonclient.httpget(__name__, metrics).splitlines()
            for c in data:
                if any(x in c for x in greps) and '#' not in c:
                    o = re.split('{|} ', c.replace('"', ''))
                    s = dict(item.split("=") for item in o[1].split(","))
                    if o[0].startswith('kube_pod_container'):
                        self.local_vars.append({'name': o[0], 'timestamp': self.timestamp, 'value': o[-1], 'reaction': -3,
                                                'extra_tag': {'container': s['container'], 'pod': s['pod']}})
                    elif o[0].startswith('kube_deployment'):
                        self.local_vars.append({'name': o[0], 'timestamp': self.timestamp, 'value': o[-1], 'reaction': 0,
                                                'extra_tag': {'deployment': s['deployment']}})
                    elif o[0].startswith('kube_endpoint_address'):
                        self.local_vars.append({'name': o[0], 'timestamp': self.timestamp, 'value': o[-1], 'reaction': 0,
                                                'extra_tag': {'endpoint': s['endpoint']}})
                    else:
                        lib.puylogger.print_message(str(a[0]))
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
