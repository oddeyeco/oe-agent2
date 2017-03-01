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
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/hadoop.ini')

hbase_master_url = config.get('HBase-Master', 'jmx')
hostname = socket.getfqdn()
cluster_name = config.get('SelfConfig', 'cluster_name')
check_type = 'hbase'


def run_hbase_master():
    try:
        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        hbase_master_stats = urllib2.urlopen(hbase_master_url, timeout=5).read()
        stats_json = json.loads(hbase_master_stats)
        stats_keys = stats_json['beans']
        node_rated_keys=('clusterRequests','GcTimeMillis')
        node_stuck_keys=('GcCount','HeapMemoryUsage')
        #mon_values={}
        rate=lib.record_rate.ValueRate()
        jsondata=lib.pushdata.JonSon()
        jsondata.prepare_data()
        timestamp = int(datetime.datetime.now().strftime("%s"))

        for stats_index in range(0, len(stats_keys)):
            for values in node_rated_keys:
                if values in stats_keys[stats_index]:
                    if values in node_rated_keys:
                        myvalue=stats_keys[stats_index][values]
                        values_rate=rate.record_value_rate('hmaster_'+values, myvalue, timestamp)
                        if values_rate >= 0:
                            jsondata.gen_data('hmaster_node_'+values, timestamp, values_rate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')
                            #mon_values.update({'hmaster_node_'+values: values_rate})

            for values in node_stuck_keys:
                if values in stats_keys[stats_index]:
                    if values == 'HeapMemoryUsage':
                        heap_metrics=('max', 'init', 'committed', 'used')
                        for heap_values in heap_metrics:
                            #mon_values.update({'hmaster_heap_'+heap_values: stats_keys[stats_index][values][heap_values]})
                            jsondata.gen_data('hmaster_heap_'+heap_values, timestamp, stats_keys[stats_index][values][heap_values], lib.pushdata.hostname, check_type, cluster_name)
                    else:
                        jsondata.gen_data('hmaster_node_'+values, timestamp, stats_keys[stats_index][values], lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')
                        #mon_values.update({'hmaster_node_'+values: stats_keys[stats_index][values]})

        #for key in mon_values.keys():
        #    jsondata.gen_data(key, timestamp, mon_values[key], lib.pushdata.hostname, check_type, cluster_name)
        jsondata.put_json()
    except Exception as e:
        lib.pushdata.print_error(__name__ , (e))
        pass
