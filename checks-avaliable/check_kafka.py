import urllib2
import os, sys
import ConfigParser
import datetime
import socket
import json

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')

jolokia_url = config.get('Kafka', 'jolokia')
hostname = socket.getfqdn()
cluster_name = config.get('SelfConfig', 'cluster_name')
check_type = 'kafka'


def run_kafka():
    try:
        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        push = __import__('pushdata')
        jsondata=push.JonSon()
        jsondata.create_data()
        timestamp = int(datetime.datetime.now().strftime("%s"))
        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        jolo_mbeans=('java.lang:type=Memory',
                     'kafka.server:type=BrokerTopicMetrics,name=BytesInPerSec',
                     'kafka.server:type=BrokerTopicMetrics,name=BytesOutPerSec',
                     'kafka.server:type=BrokerTopicMetrics,name=BytesRejectedPerSec',
                     'kafka.server:type=BrokerTopicMetrics,name=FailedFetchRequestsPerSec',
                     'kafka.server:type=BrokerTopicMetrics,name=FailedProduceRequestsPerSec',
                     'kafka.server:type=BrokerTopicMetrics,name=MessagesInPerSec',
                     'kafka.server:type=BrokerTopicMetrics,name=TotalFetchRequestsPerSec',
                     'kafka.server:type=BrokerTopicMetrics,name=TotalProduceRequestsPerSec',
                     'kafka.server:type=Fetch',
                     'kafka.server:type=Produce'
                     )
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
                            jsondata.gen_data(key, timestamp, mon_values, push.hostname, check_type, cluster_name)
                        else:
                            key='kafka_heap_'+ metr
                            mon_values=jolo_keys[heap][metr]
                            jsondata.gen_data(key, timestamp, mon_values, push.hostname, check_type, cluster_name)
            elif beans == 'kafka.server:type=Fetch':
                value= jolo_keys['queue-size']
                name = 'kafka_'+beans.split('=')[1]
                jsondata.gen_data(name, timestamp, value, push.hostname, check_type, cluster_name)
            elif beans == 'kafka.server:type=Produce':
                value= jolo_keys['queue-size']
                name = 'kafka_'+beans.split('=')[1]
                jsondata.gen_data(name, timestamp, value, push.hostname, check_type, cluster_name)
            else:
                value= jolo_keys['Count']
                name = 'kafka_'+beans.split('=')[2].split(',')[0]
                jsondata.gen_data(name, timestamp, value, push.hostname, check_type, cluster_name)
        jsondata.put_json()
        jsondata.truncate_data()

    except Exception as e:
        push = __import__('pushdata')
        push.print_error(__name__ , (e))
        pass

