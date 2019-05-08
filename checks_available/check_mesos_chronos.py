import lib.record_rate
import lib.commonclient
import lib.getconfig
import lib.puylogger
import lib.basecheck
import json

chronos_url = lib.getconfig.getparam('Mesos-Chronos', 'stats')
check_type = 'chronos'


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            chronos_stats = lib.commonclient.httpget(__name__, chronos_url)
            stats_json = json.loads(chronos_stats)
            gauges = ('jvm.memory.heap.committed', 'jvm.memory.heap.used', 'jvm.memory.non-heap.committed', 'jvm.memory.non-heap.used',
                      'jvm.threads.count', 'jvm.threads.daemon.count', 'jvm.threads.new.count', 'jvm.threads.runnable.count')

            for k in stats_json['gauges'].keys():
                if 'jvm.gc' in k:
                    gcgc = k.split('.')
                    if 'count' in k:
                        self.local_vars.append({'name': 'mesos_chronos_gc_collections', 'timestamp': self.timestamp, 'value': float(stats_json['gauges'][k]['value']), 'check_type': check_type, 'extra_tag': {'gctype': gcgc[2].lower().replace(' ', '_')}})
                    if 'time' in k:
                        self.local_vars.append({'name': 'mesos_chronos_gc_duration', 'timestamp': self.timestamp, 'value': float(stats_json['gauges'][k]['value']), 'check_type': check_type, 'extra_tag': {'gctype': gcgc[2].lower().replace(' ', '-')}})

            for gauge in gauges:
                fsto = gauge.replace('chronos.', '').\
                    replace('.gauge', '').\
                    replace('jvm.memory.heap', 'heap'). \
                    replace('jvm.memory.non-heap', 'nonheap'). \
                    replace('.bytes', ''). \
                    replace('.count', ''). \
                    replace('.', '_').replace('-', '_')
                self.local_vars.append({'name': 'mesos_chronos_' + fsto, 'timestamp': self.timestamp, 'value': stats_json['gauges'][gauge]['value'], 'check_type': check_type})
            counters = ('jobs.run.success', 'jobs.run.failure')
            for ctr in stats_json['counters'].keys():
                if 'jobs.run.success' in ctr:
                    self.local_vars.append({'name': 'mesos_chronos_jobs_success', 'timestamp': self.timestamp, 'value': float(stats_json['counters'][ctr]['count']), 'check_type': check_type, 'extra_tag': {'chronos_jobname': ctr.split('.')[3].replace(' ', '_')}})
                if 'jobs.run.failure' in ctr:
                    self.local_vars.append({'name': 'mesos_chronos_jobs_failure', 'timestamp': self.timestamp, 'value': float(stats_json['counters'][ctr]['count']), 'check_type': check_type, 'extra_tag': {'chronos_jobname': ctr.split('.')[3].replace(' ', '_')}})

        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass



