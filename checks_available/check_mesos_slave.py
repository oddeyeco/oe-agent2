import lib.record_rate
import lib.pushdata
import lib.commonclient
import lib.getconfig
import lib.puylogger
import datetime
import json

mesos_url = lib.getconfig.getparam('Mesos-Slave', 'stats')
cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_type = 'mesos'


def runcheck():
    try:
        timestamp = int(datetime.datetime.now().strftime("%s"))
        mesos_stats = lib.commonclient.httpget(__name__, mesos_url)
        jsondata = lib.pushdata.JonSon()
        jsondata.prepare_data()
        stats_json = json.loads(mesos_stats)
        metrics = ('slave/executors_terminated', 'slave/cpus_percent', 'slave/executors_running', 'slave/gpus_revocable_used',
            'slave/invalid_status_updates', 'slave/cpus_used', 'slave/disk_used', 'slave/gpus_used', 'slave/mem_percent', 'slave/tasks_running',
            'slave/frameworks_active', 'slave/mem_revocable_percent', 'slave/tasks_failed', 'slave/executors_terminating', 'slave/tasks_killing',
            'slave/disk_percent', 'slave/tasks_lost', 'slave/recovery_errors', 'slave/mem_used', 'slave/cpus_revocable_used')
        for metric in metrics:
            if metric in stats_json:
                jsondata.gen_data('mesos_'+metric.replace('/','_'), timestamp, stats_json[metric], lib.pushdata.hostname, check_type, cluster_name)
        jsondata.put_json()
    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass



