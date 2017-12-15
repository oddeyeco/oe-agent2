import lib.record_rate
import lib.commonclient
import lib.getconfig
import lib.puylogger
import lib.basecheck
import json

mesos_url = lib.getconfig.getparam('Mesos-Master', 'stats')
cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_type = 'mesos'


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            stats_json = json.loads(lib.commonclient.httpget(__name__, mesos_url))
            metrics = ('master/cpus_percent', 'master/cpus_revocable_percent', 'master/cpus_used',
                      'master/disk_percent', 'master/disk_revocable_percent', 'master/disk_used',
                      'master/event_queue_dispatches', 'master/event_queue_http_requests', 'master/event_queue_messages',
                      'master/frameworks_active', 'master/gpus_percent', 'master/gpus_used', 'master/mem_percent', 'master/mem_used',
                      'master/tasks_dropped', 'master/tasks_error', 'master/tasks_failed', 'master/tasks_finished' , 'master/tasks_gone',
                      'master/tasks_lost', 'master/tasks_running', 'master/tasks_staging', 'master/tasks_starting', 'master/tasks_unreachable',
                      'master/messages_kill_task', 'master/messages_reregister_framework', 'master/slaves_connected', 'master/slaves_connected',
                      'allocator/mesos/allocation_run_ms', 'allocator/mesos/allocation_run_ms/p99', 'registrar/state_fetch_ms', 'registrar/state_store_ms/p99')
            for metric in metrics:
                if metric in stats_json:
                    self.local_vars.append({'name': 'mesos_'+metric.replace('/','_'), 'timestamp': self.timestamp, 'value': stats_json[metric], 'check_type': check_type})
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass



