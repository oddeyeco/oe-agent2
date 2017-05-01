import lib.record_rate
import lib.pushdata
import urllib2
import os, sys
import ConfigParser
import datetime
import socket
import json

import lib.puylogger

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/bigdata.ini')


mesos_url = config.get('Mesos-Master', 'stats')
hostname = socket.getfqdn()
cluster_name = config.get('SelfConfig', 'cluster_name')
check_type = 'mesos'


def runcheck():
    try:
        mesos_stats = urllib2.urlopen(mesos_url, timeout=5).read()
        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        jsondata=lib.pushdata.JonSon()
        jsondata.prepare_data()
        stats_json = json.loads(mesos_stats)
        metrics= ('master/cpus_percent', 'master/cpus_revocable_percent', 'master/cpus_used',
                  'master/disk_percent', 'master/disk_revocable_percent', 'master/disk_used',
                  'master/event_queue_dispatches', 'master/event_queue_http_requests', 'master/event_queue_messages',
                  'master/frameworks_active', 'master/gpus_percent', 'master/gpus_used', 'master/mem_percent', 'master/mem_used',
                  'master/tasks_dropped', 'master/tasks_error', 'master/tasks_failed', 'master/tasks_finished' , 'master/tasks_gone',
                  'master/tasks_lost', 'master/tasks_running', 'master/tasks_staging', 'master/tasks_starting', 'master/tasks_unreachable',
                  'master/messages_kill_task', 'master/messages_reregister_framework', 'master/slaves_connected', 'master/slaves_connected',
                  'allocator/mesos/allocation_run_ms', 'allocator/mesos/allocation_run_ms/p99', 'registrar/state_fetch_ms', 'registrar/state_store_ms/p99')
        for metric in metrics:
            timestamp = int(datetime.datetime.now().strftime("%s"))
            jsondata.gen_data('mesos_'+metric.replace('/','_'), timestamp, stats_json[metric], lib.pushdata.hostname, check_type, cluster_name)
        jsondata.put_json()
    except Exception as e:
        lib.pushdata.print_error(__name__ , (e))
        pass



