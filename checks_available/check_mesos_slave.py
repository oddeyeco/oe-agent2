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


mesos_url = config.get('Mesos-Slave', 'stats')
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
        metrics= ('slave/executors_terminated', 'slave/cpus_percent', 'slave/executors_running', 'slave/gpus_revocable_used',
            'slave/invalid_status_updates', 'slave/cpus_used', 'slave/disk_used', 'slave/gpus_used', 'slave/mem_percent', 'slave/tasks_running',
            'slave/frameworks_active', 'slave/mem_revocable_percent', 'slave/tasks_failed', 'slave/executors_terminating', 'slave/tasks_killing',
            'slave/disk_percent', 'slave/tasks_lost', 'slave/recovery_errors', 'slave/mem_used', 'slave/cpus_revocable_used')
        for metric in metrics:
            timestamp = int(datetime.datetime.now().strftime("%s"))
            jsondata.gen_data('mesos_'+metric.replace('/','_'), timestamp, stats_json[metric], lib.pushdata.hostname, check_type, cluster_name)
        jsondata.put_json()
    except Exception as e:
        lib.pushdata.print_error(__name__ , (e))
        pass



