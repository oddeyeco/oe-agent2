import lib.record_rate
import lib.commonclient
import lib.getconfig
import lib.puylogger
import lib.basecheck
import json

marathon_url = lib.getconfig.getparam('Marathon', 'stats')
check_type = 'marathon'


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            marathon_stats = lib.commonclient.httpget(__name__, marathon_url)
            stats_json = json.loads(marathon_stats)
            gauges = ('marathon.apps.active.gauge', 'marathon.deployments.active.gauge', 'marathon.instances.running.gauge', 'marathon.instances.launch-overdue.gauge',
                      'marathon.pods.active.gauge', 'marathon.http.requests.active.gauge', 'marathon.groups.active.gauge',
                      'marathon.http.event-streams.active.gauge', 'marathon.instances.launch-overdue.gauge', 'marathon.instances.staged.gauge',
                      'marathon.jvm.memory.heap.committed.gauge.bytes', 'marathon.jvm.memory.heap.used.gauge.bytes',
                      'marathon.jvm.memory.non-heap.committed.gauge.bytes', 'marathon.jvm.memory.non-heap.used.gauge.bytes')

            for k in stats_json['gauges'].keys():
                if 'marathon.jvm.gc' in k:
                    gcgc = k.split('.')
                    if len(gcgc) is 6:
                        self.local_vars.append({'name': 'marathon_gc_collections', 'timestamp': self.timestamp, 'value': float(stats_json['gauges'][k]['value']), 'check_type': check_type, 'extra_tag': {'gctype': gcgc[3]}})
                    if len(gcgc) is 8:
                        self.local_vars.append({'name': 'marathon_gc_duration', 'timestamp': self.timestamp, 'value': float(stats_json['gauges'][k]['value']), 'check_type': check_type, 'extra_tag': {'gctype': gcgc[3]}})

            for gauge in gauges:
                fsto = gauge.replace('marathon.', '').\
                    replace('.gauge', '').\
                    replace('jvm.memory.heap', 'heap'). \
                    replace('jvm.memory.non-heap', 'nonheap'). \
                    replace('.bytes', '').\
                    replace('.', '_').replace('-', '_')
                self.local_vars.append({'name': 'marathon_' + fsto, 'timestamp': self.timestamp, 'value': stats_json['gauges'][gauge]['value'], 'check_type': check_type})

        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass



