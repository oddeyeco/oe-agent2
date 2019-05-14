import lib.record_rate
import lib.commonclient
import lib.getconfig
import lib.puylogger
import lib.basecheck
import json

consul_url = lib.getconfig.getparam('Hashicorp-Consul', 'telemetery')
detailed = lib.getconfig.getparam('Hashicorp-Consul', 'detailed')
getrated = lib.getconfig.getparam('Hashicorp-Consul', 'getrates')

check_type = 'consul'


class Check(lib.basecheck.CheckBase):
    def precheck(self):
        try:
            consul_stats = lib.commonclient.httpget(__name__, consul_url)
            stats_json = json.loads(consul_stats)
            basestats = ('consul.runtime.alloc_bytes', 'consul.runtime.free_count', 'consul.runtime.heap_objects', 'consul.runtime.malloc_count'
                         'consul.runtime.num_goroutines', 'consul.runtime.sys_bytes', 'consul.runtime.total_gc_pause_ns', 'consul.runtime.total_gc_runs', 'consul.session_ttl.active')

            rates = ('consul.consul.job_summary.queued', 'consul.consul.job_summary.complete', 'consul.consul.job_summary.failed',
                           'consul.consul.job_summary.running', 'consul.consul.job_summary.starting', 'consul.consul.job_summary.lost')

            for index in range(0, len(stats_json['Gauges'])):
                if stats_json['Gauges'][index]['Name'] in basestats:
                    self.local_vars.append({'name': stats_json['Gauges'][index]['Name'].replace('.', '_').replace('-', '_').lower(), 'timestamp': self.timestamp, 'value': stats_json['Gauges'][index]['Value'], 'check_type': check_type})

            for index in range(0, len(stats_json['Counters'])):
                self.local_vars.append({'name': stats_json['Counters'][index]['Name'].replace('.', '_').replace('-', '_').lower(), 'timestamp': self.timestamp, 'value': float(stats_json['Counters'][index]['Rate']), 'check_type': check_type})

            if detailed:
                if getrated:
                    for index in range(0, len(stats_json['Samples'])):
                        self.local_vars.append({'name': stats_json['Samples'][index]['Name'].replace('.', '_').replace('-', '_').lower(), 'timestamp': self.timestamp, 'value': float(stats_json['Samples'][index]['Rate']), 'check_type': check_type})
                else:
                    for index in range(0, len(stats_json['Samples'])):
                        self.local_vars.append({'name': stats_json['Samples'][index]['Name'].replace('.', '_').replace('-', '_').lower(), 'timestamp': self.timestamp, 'value': float(stats_json['Samples'][index]['Count']), 'check_type': check_type})

        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass



