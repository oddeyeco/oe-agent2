import lib.record_rate
import lib.commonclient
import lib.getconfig
import lib.puylogger
import lib.basecheck
import json

nomad_url = lib.getconfig.getparam('Hashicorp-Nomad', 'telemetery')
jobstats = lib.getconfig.getparam('Hashicorp-Nomad', 'jobstats')
check_type = 'nomad'


class Check(lib.basecheck.CheckBase):
    def precheck(self):
        try:
            nomad_stats = lib.commonclient.httpget(__name__, nomad_url)
            stats_json = json.loads(nomad_stats)
            basestats = ('nomad.client.allocated.cpu', 'nomad.client.unallocated.cpu', 'nomad.client.allocated.memory', 'nomad.client.unallocated.memory',
                         'nomad.client.allocated.disk', 'nomad.client.unallocated.disk', 'nomad.client.allocated.network', 'nomad.client.unallocated.network',
                         'nomad.runtime.num_goroutines', 'nomad.runtime.alloc_bytes', 'nomad.runtime.heap_objects')
            serverstats = ('nomad.nomad.job_summary.queued', 'nomad.nomad.job_summary.complete', 'nomad.nomad.job_summary.failed',
                           'nomad.nomad.job_summary.running', 'nomad.nomad.job_summary.starting', 'nomad.nomad.job_summary.lost')

            for index in range(0, len(stats_json['Gauges'])):
                if stats_json['Gauges'][index]['Name'] in basestats:
                    self.local_vars.append({'name': stats_json['Gauges'][index]['Name'].replace('.', '_'), 'timestamp': self.timestamp, 'value': stats_json['Gauges'][index]['Value'], 'check_type': check_type})
                if stats_json['Gauges'][index]['Name'] in serverstats and jobstats:
                    self.local_vars.append(
                        {'name': stats_json['Gauges'][index]['Name'].replace('nomad.nomad', 'nomad').replace('.', '_'),
                         'timestamp': self.timestamp, 'value': stats_json['Gauges'][index]['Value'],
                         'check_type': check_type, 'extra_tag': {'nomad_jobname': stats_json['Gauges'][index]['Labels']['job'].replace('/', '_')}})
                if stats_json['Gauges'][index]['Name'] == 'nomad.nomad.heartbeat.active':
                    self.local_vars.append({'name': stats_json['Gauges'][index]['Name'].replace('nomad.nomad', 'nomad').replace('.', '_'), 'timestamp': self.timestamp, 'value': stats_json['Gauges'][index]['Value'], 'check_type': check_type})
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass