import lib.record_rate
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
        local_vars = []
        hadoop_namenode_stats = json.loads(lib.commonclient.httpget(__name__, hadoop_namenode_url))
        rate = lib.record_rate.ValueRate()
        timestamp = int(datetime.datetime.now().strftime("%s"))
        stats_keys = hadoop_namenode_stats['beans']
        node_stack_keys = ('CapacityTotal', 'CapacityUsed', 'NonDfsUsedSpace', 'CapacityRemaining','PercentRemaining', 'OpenFileDescriptorCount')
        node_rated_keys = ('CreateFileOps', 'GetBlockLocations', 'FilesRenamed', 'GetListingOps', 'DeleteFileOps', 'FilesDeleted', 'FileInfoOps', 'AddBlockOps', 'TransactionsNumOps', 'ReceivedBytes', 'SentBytes')
        mon_values = {}

        for stats_index in range(0, len(stats_keys)):

            for v in ('NonHeapMemoryUsage','HeapMemoryUsage'):
                if v in stats_keys[stats_index]:
                    heap_metrics = ('max', 'init', 'committed', 'used')
                    name = v.replace('Node', '').replace('Usage', '').replace('Memory', '').lower()
                    for heap_values in heap_metrics:
                        mon_values.update({'namenode_' + name + '_' + heap_values: stats_keys[stats_index][v][heap_values]})

            if 'LastGcInfo' in stats_keys[stats_index]:
                if type(stats_keys[stats_index]['LastGcInfo']) is dict:
                    mon_values.update({'namenode_lastgc_duration': stats_keys[stats_index]['LastGcInfo']['duration']})

            for values in node_stack_keys:
                if values in stats_keys[stats_index]:
                    mon_values.update({'namenode_' + values.lower(): stats_keys[stats_index][values]})
            for values in node_rated_keys:
                if values in stats_keys[stats_index]:
                    stack_value = stats_keys[stats_index][values]
                    reqrate = rate.record_value_rate('namenode_'+values, stack_value, timestamp)
                    local_vars.append({'name': 'namenode_'+values.lower(), 'timestamp': timestamp, 'value': reqrate, 'check_type': check_type, 'chart_type': 'Rate'})

        for key in list(mon_values.keys()):
            local_vars.append({'name': key.lower(), 'timestamp': timestamp, 'value': mon_values[key], 'check_type': check_type})
        return local_vars
    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass

