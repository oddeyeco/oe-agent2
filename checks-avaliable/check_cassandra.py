import urllib2
import os, sys
import ConfigParser
import datetime
import socket
import json


config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')

jolokia_url = config.get('Cassandra', 'jolokia')
hostname = socket.getfqdn()
cluster_name = config.get('SelfConfig', 'cluster_name')
check_type = 'cassandra'
alert_level = -3

def run_cassandra():
    try:
        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        push = __import__('pushdata')
        value_rate= __import__('record_rate')
        jsondata=push.JonSon()
        jsondata.create_data()
        rate=value_rate.ValueRate()
        timestamp = int(datetime.datetime.now().strftime("%s"))

        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        jolo_mbeans=('java.lang:type=Memory', 'org.apache.cassandra.db:type=Caches',
                     'org.apache.cassandra.transport:type=Native-Transport-Requests',
                     'org.apache.cassandra.request:type=*',
                     'org.apache.cassandra.metrics:type=Compaction,name=*',
                     'org.apache.cassandra.internal:type=GossipStage')
        for beans in jolo_mbeans:
            jolo_url=urllib2.urlopen(jolokia_url+'/'+beans, timeout=5).read()
            jolo_json = json.loads(jolo_url)
            jolo_keys = jolo_json['value']
            if beans == 'org.apache.cassandra.metrics:type=Compaction,name=*':
                mon_values=jolo_keys['org.apache.cassandra.metrics:name=PendingTasks,type=Compaction']['Value']
                name='cassa_pending_compactions'
                jsondata.gen_data(name, timestamp, mon_values, push.hostname, check_type, cluster_name)

            if beans == 'java.lang:type=Memory':
                metr_name=('used', 'committed')
                heap_type=('NonHeapMemoryUsage', 'HeapMemoryUsage')
                for heap in heap_type:
                    for metr in metr_name:
                        if heap == 'NonHeapMemoryUsage':
                            key='cassa_nonheap_'+ metr
                            mon_values=jolo_keys[heap][metr]
                            jsondata.gen_data(key, timestamp, mon_values, push.hostname, check_type, cluster_name, alert_level)
                        else:
                            key='cassa_heap_'+ metr
                            mon_values=jolo_keys[heap][metr]
                            jsondata.gen_data(key, timestamp, mon_values, push.hostname, check_type, cluster_name, alert_level)
            elif beans == 'org.apache.cassandra.db:type=Caches':
                needed_stats=('RowCacheHits','KeyCacheHits','RowCacheRequests','KeyCacheRequests')
                for my_name in jolo_keys:
                    my_value=jolo_keys[my_name]
                    if my_name in needed_stats and my_value > 0:
                        name='cassa_'+my_name
                        value_rate=rate.record_value_rate(name, my_value, timestamp)
                        jsondata.gen_data(name, timestamp, value_rate, push.hostname, check_type, cluster_name)
            request_keys=('RequestResponseStage','ReadStage','MutationStage')
            if beans == 'org.apache.cassandra.request:type=*':
                for key in request_keys:
                    name = 'cassa_' + key
                    value = jolo_keys['org.apache.cassandra.request:type='+key]['CompletedTasks']
                    value_rate=rate.record_value_rate(name, value, timestamp)
                    jsondata.gen_data(name, timestamp, value_rate, push.hostname, check_type, cluster_name)
            if beans == 'org.apache.cassandra.transport:type=Native-Transport-Requests':
                name = 'cassa_Native-Transport-Requests'
                value = jolo_json['value']['CompletedTasks']
                value_rate = rate.record_value_rate(name, value, timestamp)
                jsondata.gen_data(name, timestamp, value_rate, push.hostname, check_type, cluster_name)
        jsondata.put_json()
        jsondata.truncate_data()

    except Exception as e:
        push = __import__('pushdata')
        push.print_error(__name__ , (e))
        pass

