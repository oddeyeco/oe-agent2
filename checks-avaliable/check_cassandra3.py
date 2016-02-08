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


def run_cassandra3():
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
                     'org.apache.cassandra.metrics:name=PreparedStatementsCount,type=CQL',
                     'org.apache.cassandra.metrics:type=CQL,name=RegularStatementsExecuted',
                     'org.apache.cassandra.metrics:type=Cache,scope=KeyCache,name=Hits',
                     'org.apache.cassandra.metrics:type=Cache,scope=KeyCache,name=Requests',
                     'org.apache.cassandra.metrics:type=Cache,scope=RowCache,name=Hits',
                     'org.apache.cassandra.metrics:type=Cache,scope=RowCache,name=Requests'
                    )

        for beans in jolo_mbeans:
            jolo_url=urllib2.urlopen(jolokia_url+'/'+beans, timeout=5).read()
            jolo_json = json.loads(jolo_url)
            jolo_keys = jolo_json['value']
            if beans == 'java.lang:type=Memory':
                metr_name=('used', 'committed')
                heap_type=('NonHeapMemoryUsage', 'HeapMemoryUsage')
                for heap in heap_type:
                    for metr in metr_name:
                        if heap == 'NonHeapMemoryUsage':
                            key='cassa_nonheap_'+ metr
                            mon_values=jolo_keys[heap][metr]
                            jsondata.gen_data(key, timestamp, mon_values, push.hostname, check_type, cluster_name)
                        else:
                            key='cassa_heap_'+ metr
                            mon_values=jolo_keys[heap][metr]
                            jsondata.gen_data(key, timestamp, mon_values, push.hostname, check_type, cluster_name)
            elif beans == 'org.apache.cassandra.metrics:name=PreparedStatementsCount,type=CQL':
                value= jolo_keys['Value']
                name = 'cassa_cql_PreparedStatements'
                if value is 0:
                    jsondata.gen_data(name, timestamp, value, push.hostname, check_type, cluster_name)
                else:
                    value_rate=rate.record_value_rate(name, value, timestamp)
                    jsondata.gen_data(name, timestamp, value_rate, push.hostname, check_type, cluster_name)
            elif beans == 'org.apache.cassandra.metrics:type=CQL,name=RegularStatementsExecuted':
                value_rate=rate.record_value_rate(name, value, timestamp)
                jsondata.gen_data(name, timestamp, value_rate, push.hostname, check_type, cluster_name)
                value= jolo_keys['Count']
                name = 'cassa_cql_RegularStatement'
            similars=('org.apache.cassandra.metrics:type=Cache,scope=KeyCache,name=Hits',
                      'org.apache.cassandra.metrics:type=Cache,scope=KeyCache,name=Requests',
                      'org.apache.cassandra.metrics:type=Cache,scope=RowCache,name=Hits',
                      'org.apache.cassandra.metrics:type=Cache,scope=RowCache,name=Requests'
                      )
            if beans in similars:
                name = 'cassa_'+beans.split('=')[2].split(',')[0]+'_'+beans.split('=')[3]
                value= jolo_keys['Count']
                value_rate=rate.record_value_rate(name, value, timestamp)
                jsondata.gen_data(name, timestamp, value_rate, push.hostname, check_type, cluster_name)
        jsondata.put_json()
        jsondata.truncate_data()

    except Exception as e:
        push = __import__('pushdata')
        push.print_error(__name__ , (e))
        pass

