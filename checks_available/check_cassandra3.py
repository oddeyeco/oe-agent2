import urllib2
import os, sys
import ConfigParser
import datetime
import socket
import json

import lib.pushdata
import lib.record_rate




config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/bigdata.ini')

jolokia_url = config.get('Cassandra', 'jolokia')
hostname = socket.getfqdn()
cluster_name = config.get('SelfConfig', 'cluster_name')
check_type = 'cassandra'
reaction=-3

def runcheck():
    try:
        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        jsondata=lib.pushdata.JonSon()
        jsondata.prepare_data()
        rate=lib.record_rate.ValueRate()
        timestamp = int(datetime.datetime.now().strftime("%s"))

        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        java_lang_metrics=json.loads(urllib2.urlopen(jolokia_url+'/java.lang:type=Memory', timeout=5).read())
        cassa_cql_metrics=json.loads(urllib2.urlopen(jolokia_url+'/org.apache.cassandra.metrics:type=CQL,name=*', timeout=5).read())
        cassa_cache_metrics=json.loads(urllib2.urlopen(jolokia_url+'/org.apache.cassandra.metrics:type=Cache,scope=*,name=*', timeout=5).read())
        cassa_copmaction=json.loads(urllib2.urlopen(jolokia_url+'/org.apache.cassandra.metrics:type=Compaction,name=*', timeout=5).read())

        jmetr_name = ('used', 'committed')
        jheap_type = ('NonHeapMemoryUsage', 'HeapMemoryUsage')
        for heap in jheap_type:
            for metr in jmetr_name:
                if heap == 'NonHeapMemoryUsage':
                    key = 'cassa_nonheap_' + metr
                    mon_values = java_lang_metrics['value'][heap][metr]
                    jsondata.gen_data(key, timestamp, mon_values, lib.pushdata.hostname, check_type, cluster_name, reaction)
                else:
                    key = 'cassa_heap_' + metr
                    mon_values = java_lang_metrics['value'][heap][metr]
                    jsondata.gen_data(key, timestamp, mon_values, lib.pushdata.hostname, check_type, cluster_name, reaction)

        cql_statemets = ('PreparedStatementsExecuted', 'RegularStatementsExecuted')
        for cql_statement in cql_statemets:
            mon_value = cassa_cql_metrics['value']['org.apache.cassandra.metrics:name=' + cql_statement + ',type=CQL']['Count']
            mon_name='cassa_cql_'+cql_statement
            if mon_value is not None:
                if mon_value is 0:
                    jsondata.gen_data(mon_name, timestamp, mon_value, lib.pushdata.hostname, check_type, cluster_name)
                else:
                    value_rate=rate.record_value_rate('cql_'+mon_name, mon_value, timestamp)
                    jsondata.gen_data(mon_name, timestamp, value_rate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')

        cache_metrics = ('Hits,scope=KeyCache', 'Requests,scope=KeyCache', 'Requests,scope=RowCache', 'Hits,scope=RowCache')
        for cache_metric in cache_metrics:
            mon_value = cassa_cache_metrics['value']['org.apache.cassandra.metrics:name=' + cache_metric + ',type=Cache']['OneMinuteRate']
            mon_name= 'cassa_'+ str(cache_metric).replace(',scope=', '_')
            jsondata.gen_data(mon_name, timestamp, mon_value, lib.pushdata.hostname, check_type, cluster_name)

        copaction_tasks=cassa_copmaction['value']['org.apache.cassandra.metrics:name=PendingTasks,type=Compaction']['Value']
        jsondata.gen_data('cassa_compaction_pending', timestamp, copaction_tasks, lib.pushdata.hostname, check_type, cluster_name)

        jsondata.put_json()

    except Exception as e:
        lib.pushdata.print_error(__name__ , (e))
        pass