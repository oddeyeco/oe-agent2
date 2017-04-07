import lib.record_rate
import lib.pushdata
import urllib2
import os, sys
import ConfigParser
import datetime
import socket
import json

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/mq.ini')


jolokia_url = config.get('Kafka', 'jolokia')
TYPE= config.get('Kafka', 'gctype')
hostname = socket.getfqdn()
cluster_name = config.get('SelfConfig', 'cluster_name')
check_type = 'kafka'


if TYPE == 'G1':
    CMS=False
    G1=True
if TYPE == 'CMS':
    CMS=True
    G1=False

def runcheck():
    try:
        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        jsondata=lib.pushdata.JonSon()
        jsondata.prepare_data()
        rate=lib.record_rate.ValueRate()
        timestamp = int(datetime.datetime.now().strftime("%s"))
        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        jolo_mbeans=('java.lang:type=Memory',
                     'kafka.server:type=BrokerTopicMetrics,name=*',
                     'kafka.network:name=RequestsPerSec,request=FetchConsumer,type=RequestMetrics',
                     'kafka.network:name=RequestsPerSec,request=Produce,type=RequestMetrics'
                     )
        if G1 is True:
            gc_young_json = json.load(urllib2.urlopen(jolokia_url + '/java.lang:name=G1%20Young%20Generation,type=GarbageCollector', timeout=15))
            gc_old_json = json.load(urllib2.urlopen(jolokia_url + '/java.lang:name=G1%20Old%20Generation,type=GarbageCollector', timeout=15))
            for name in ('LastGcInfo','CollectionTime','CollectionCount'):
                value = gc_old_json['value'][name]
                if value is None:
                    value = 0
                if name == 'CollectionTime':
                    values_rate = rate.record_value_rate(name, value, timestamp)
                    key = 'kafka_gc_old_' + name
                    jsondata.gen_data(key, timestamp, values_rate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')
                else:
                    key = 'kafka_gc_old_' + name
                    jsondata.gen_data(key, timestamp, value, lib.pushdata.hostname, check_type, cluster_name)
            for name in ('LastGcInfo', 'CollectionTime', 'CollectionCount'):
                if name == 'LastGcInfo':
                    vl = gc_young_json['value'][name]['duration']
                    if vl is None:
                        vl = 0
                    key = 'kafka_gc_young_' + name
                    jsondata.gen_data(key, timestamp, vl, lib.pushdata.hostname, check_type, cluster_name)
                if name == 'CollectionTime':
                    vl = gc_young_json['value'][name]
                    if vl is None:
                        vl = 0
                    key = 'kafka_gc_young_' + name
                    vl_rate = rate.record_value_rate(key, vl, timestamp)
                    jsondata.gen_data(key, timestamp, vl_rate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')
                if name == 'CollectionCount':
                    vl = gc_young_json['value'][name]
                    if vl is None:
                        vl = 0
                    key = 'kafka_gc_young_' + name
                    jsondata.gen_data(key, timestamp, vl, lib.pushdata.hostname, check_type, cluster_name)

        for beans in jolo_mbeans:
            jolo_url=urllib2.urlopen(jolokia_url+'/'+beans, timeout=15).read()
            jolo_json = json.loads(jolo_url)
            jolo_keys = jolo_json['value']
            if beans == 'java.lang:type=Memory':
                metr_name=('used', 'committed')
                heap_type=('NonHeapMemoryUsage', 'HeapMemoryUsage')
                for heap in heap_type:
                    for metr in metr_name:
                        if heap == 'NonHeapMemoryUsage':
                            key='kafka_nonheap_'+ metr
                            mon_values=jolo_keys[heap][metr]
                            jsondata.gen_data(key, timestamp, mon_values, lib.pushdata.hostname, check_type, cluster_name)
                        else:
                            key='kafka_heap_'+ metr
                            mon_values=jolo_keys[heap][metr]
                            jsondata.gen_data(key, timestamp, mon_values, lib.pushdata.hostname, check_type, cluster_name)
            elif beans == 'kafka.server:type=Fetch':
                value= jolo_keys['queue-size']
                name = 'kafka_'+beans.split('=')[1]
                values_rate = rate.record_value_rate(name, value, timestamp)
                if values_rate >= 0:
                    jsondata.gen_data(name, timestamp, values_rate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')

            elif beans == 'kafka.server:type=Produce':
                value= jolo_keys['queue-size']
                name = 'kafka_'+beans.split('=')[1]
                values_rate = rate.record_value_rate(name, value, timestamp)
                if values_rate >= 0:
                    jsondata.gen_data(name, timestamp, values_rate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')

            elif beans == 'kafka.network:name=RequestsPerSec,request=FetchConsumer,type=RequestMetrics':
                minute_value = jolo_keys['OneMinuteRate']
                value = minute_value / 60
                key = 'kafka_RequestMetrics_FetchConsumer'
                jsondata.gen_data(key, timestamp, value, lib.pushdata.hostname, check_type, cluster_name)
            elif beans == 'kafka.network:name=RequestsPerSec,request=Produce,type=RequestMetrics':
                minute_value = jolo_keys['OneMinuteRate']
                value = minute_value / 60
                key = 'kafka_RequestMetrics_Produce'
                jsondata.gen_data(key, timestamp, value, lib.pushdata.hostname, check_type, cluster_name)

            elif beans == 'kafka.server:type=BrokerTopicMetrics,name=*':
                beans=('BytesInPerSec', 'BytesOutPerSec', 'BytesRejectedPerSec', 'FailedFetchRequestsPerSec', 'FailedProduceRequestsPerSec','MessagesInPerSec')
                for bean in beans :
                    m='kafka.server:name='+bean+',type=BrokerTopicMetrics'
                    value= jolo_json['value'][m]['OneMinuteRate']
                    jsondata.gen_data('kafka_'+bean, timestamp, value, lib.pushdata.hostname, check_type, cluster_name)
        jsondata.put_json()

    except Exception as e:
        lib.pushdata.print_error(__name__ , (e))
        pass


