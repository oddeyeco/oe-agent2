import lib.record_rate
import lib.pushdata
import lib.getconfig
import lib.commonclient
import lib.puylogger
import datetime
import json




hadoop_namenode_url = lib.getconfig.getparam('Hadoop-NameNode', 'jmx')
cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_type = 'hdfs'


def runcheck():
    try:
        hadoop_namenode_stats = json.loads(lib.commonclient.httpget(__name__, hadoop_namenode_url))
        rate = lib.record_rate.ValueRate()
        jsondata = lib.pushdata.JonSon()
        jsondata.prepare_data()
        timestamp = int(datetime.datetime.now().strftime("%s"))

        stats_keys = hadoop_namenode_stats['beans']
        node_stack_keys = ('NonHeapMemoryUsage','HeapMemoryUsage', 'CapacityTotal', 'CapacityUsed', 'NonDfsUsedSpace', 'CapacityRemaining','PercentRemaining', 'OpenFileDescriptorCount', 'LastGcInfo')
        node_rated_keys = ('CreateFileOps', 'GetBlockLocations', 'FilesRenamed', 'GetListingOps', 'DeleteFileOps', 'FilesDeleted', 'FileInfoOps', 'AddBlockOps', 'TransactionsNumOps', 'ReceivedBytes', 'SentBytes')
        mon_values = {}

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
                    jsondata.gen_data('namenode_'+values.lower(), timestamp, reqrate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')

        for key in mon_values.keys():
            jsondata.gen_data(key.lower(), timestamp, mon_values[key], lib.pushdata.hostname, check_type, cluster_name)
        jsondata.put_json()
    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass

