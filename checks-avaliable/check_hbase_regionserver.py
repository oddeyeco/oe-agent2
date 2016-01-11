import urllib2
import os, sys
import ConfigParser
import datetime
import socket
import json


config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')

hbase_region_url = config.get('HBase-Region', 'jmx')
hostname = socket.getfqdn()
cluster_name = config.get('SelfConfig', 'cluster_name')
check_type = 'hbase'


def run_hbase():
    try:
        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        hbase_region_stats = urllib2.urlopen(hbase_region_url, timeout=5).read()
        stats_json = json.loads(hbase_region_stats)
        stats_keys = stats_json['beans']
        node_rated_keys=('totalRequestCount','readRequestCount','writeRequestCount', 'Delete_num_ops', 'Mutate_num_ops', 'FlushTime_num_ops','GcTimeMillis')
        node_stuck_keys=('GcCount','HeapMemoryUsage')
        mon_values={}
        push = __import__('pushdata')
        value_rate= __import__('record_rate')
        rate=value_rate.ValueRate()
        jsondata=push.JonSon()
        jsondata.create_data()
        timestamp = int(datetime.datetime.now().strftime("%s"))

        for stats_index in range(0, len(stats_keys)):
            for values in node_rated_keys:
                if values in stats_keys[stats_index]:
                    if values in node_rated_keys:
                        myvalue=stats_keys[stats_index][values]
                        values_rate=rate.record_value_rate('hregion_'+values, myvalue, timestamp)
                        if values_rate >= 0:
                            mon_values.update({'hregion_node_'+values: values_rate})

            for values in node_stuck_keys:
                if values in stats_keys[stats_index]:
                    if values == 'HeapMemoryUsage':
                        heap_metrics=('max', 'init', 'committed', 'used')
                        for heap_values in heap_metrics:
                            mon_values.update({'hregion_heap_'+heap_values: stats_keys[stats_index][values][heap_values]})
                    else:
                        mon_values.update({'hregion_node_'+values: stats_keys[stats_index][values]})

        for key in mon_values.keys():
            jsondata.gen_data(key, timestamp, mon_values[key], push.hostname, check_type, cluster_name)
        jsondata.put_json()
        jsondata.truncate_data()
    except Exception as e:
        push = __import__('pushdata')
        push.print_error(e)
        pass
