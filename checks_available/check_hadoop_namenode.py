import lib.record_rate
import lib.pushdata
import pycurl
import os, sys
import ConfigParser
import datetime
import socket
import json



config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/hadoop.ini')

hadoop_namenode_url = config.get('Hadoop-NameNode', 'jmx')
hostname = socket.getfqdn()
cluster_name = config.get('SelfConfig', 'cluster_name')
check_type = 'hdfs'

class buffer:
   def __init__(self):
       self.contents = ''

   def body_callback(self, buf):
       self.contents = self.contents + buf



def runcheck():
    try:
        t = buffer()
        c = pycurl.Curl()
        c.setopt(c.URL, hadoop_namenode_url)
        c.setopt(c.WRITEFUNCTION, t.body_callback)
        c.setopt(c.FAILONERROR, True)
        c.setopt(pycurl.CONNECTTIMEOUT, 10)
        c.setopt(pycurl.TIMEOUT, 10)
        c.setopt(pycurl.NOSIGNAL, 5)
        c.perform()
        c.close()

        hadoop_namenode_stats=json.loads(t.contents)

        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        rate=lib.record_rate.ValueRate()
        jsondata=lib.pushdata.JonSon()
        jsondata.prepare_data()
        timestamp = int(datetime.datetime.now().strftime("%s"))

        stats_keys = hadoop_namenode_stats['beans']
        node_stack_keys=('NonHeapMemoryUsage','HeapMemoryUsage', 'CapacityTotal', 'CapacityUsed', 'NonDfsUsedSpace', 'CapacityRemaining','PercentRemaining', 'OpenFileDescriptorCount', 'LastGcInfo')
        node_rated_keys=('CreateFileOps', 'GetBlockLocations', 'FilesRenamed', 'GetListingOps', 'DeleteFileOps', 'FilesDeleted', 'FileInfoOps', 'AddBlockOps', 'TransactionsNumOps', 'ReceivedBytes', 'SentBytes')
        mon_values={}

        for stats_index in range(0, len(stats_keys)):
            for values in node_stack_keys:
                if values in stats_keys[stats_index]:
                    if values == 'HeapMemoryUsage':
                        heap_metrics=('max', 'init', 'committed', 'used')
                        for heap_values in heap_metrics:
                            mon_values.update({'namenode_heap_'+heap_values: stats_keys[stats_index][values][heap_values]})
                    if values == 'NonHeapMemoryUsage':
                        heap_metrics=('max', 'init', 'committed', 'used')
                        for heap_values in heap_metrics:
                            mon_values.update({'namenode_nonheap_'+heap_values: stats_keys[stats_index][values][heap_values]})
                    if values == 'Capacity':
                        mon_values.update({'namenode_capacity': stats_keys[stats_index][values]})
                    if values == 'DfsUsed':
                        mon_values.update({'namenode_dfsused': stats_keys[stats_index][values]})
                    if values == 'OpenFileDescriptorCount':
                        mon_values.update({'namenode_openfiles': stats_keys[stats_index][values]})
                    if values == 'Remaining':
                        mon_values.update({'namenode_space_remaining': stats_keys[stats_index][values]})
                    if values == 'LastGcInfo':
                        if type(stats_keys[stats_index][values]) is dict:
                            mon_values.update({'namenode_lastgc_duration': stats_keys[stats_index][values]['duration']})
            for values in node_rated_keys:
                if values in stats_keys[stats_index]:
                    stack_value=stats_keys[stats_index][values]
                    reqrate=rate.record_value_rate('namenode_'+values, stack_value, timestamp)
                    jsondata.gen_data('namenode_'+values, timestamp, reqrate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')

        for key in mon_values.keys():
            jsondata.gen_data(key, timestamp, mon_values[key], lib.pushdata.hostname, check_type, cluster_name)
        jsondata.put_json()
        #print mon_values
    except Exception as e:
        lib.pushdata.print_error(__name__ , (e))
        pass

