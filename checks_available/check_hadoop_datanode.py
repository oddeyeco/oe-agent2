import lib.record_rate
import lib.commonclient
import lib.getconfig
import lib.puylogger
import datetime
import json

hadoop_datanode_url = lib.getconfig.getparam('Hadoop-Datanode', 'jmx')
cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_type = 'hdfs'
reaction = -3
warn_level = 20


def runcheck():
    local_vars = []
    try:
        hadoop_datanode_stats = json.loads(lib.commonclient.httpget(__name__, hadoop_datanode_url))
        rate = lib.record_rate.ValueRate()
        timestamp = int(datetime.datetime.now().strftime("%s"))

        stats_keys = hadoop_datanode_stats['beans']
        node_stack_keys = ('NonHeapMemoryUsage','HeapMemoryUsage', 'Capacity', 'DfsUsed', 'Remaining', 'OpenFileDescriptorCount', 'LastGcInfo')
        node_rated_keys = ('BytesRead', 'BytesWritten', 'TotalReadTime', 'TotalWriteTime')
        mon_values = {}

        for stats_index in range(0, len(stats_keys)):
            for values in node_stack_keys:
                if values in stats_keys[stats_index]:
                    if values == 'HeapMemoryUsage':
                        heap_metrics=('max', 'init', 'committed', 'used')
                        for heap_values in heap_metrics:
                            mon_values.update({'datanode_heap_'+heap_values: stats_keys[stats_index][values][heap_values]})
                    if values == 'NonHeapMemoryUsage':
                        heap_metrics=('max', 'init', 'committed', 'used')
                        for heap_values in heap_metrics:
                            mon_values.update({'datanode_nonheap_'+heap_values: stats_keys[stats_index][values][heap_values]})
                    if values == 'Capacity':
                        mon_values.update({'datanode_capacity': stats_keys[stats_index][values]})
                    if values == 'DfsUsed':
                        mon_values.update({'datanode_dfsused': stats_keys[stats_index][values]})
                    if values == 'OpenFileDescriptorCount':
                        mon_values.update({'datanode_openfiles': stats_keys[stats_index][values]})
                    if values == 'Remaining':
                        mon_values.update({'datanode_space_remaining': stats_keys[stats_index][values]})
                    if values == 'LastGcInfo':
                        if type(stats_keys[stats_index][values]) is dict:
                            mon_values.update({'datanode_lastgc_duration': stats_keys[stats_index][values]['duration']})
            for values in node_rated_keys:
                if values in stats_keys[stats_index]:
                    stack_value = stats_keys[stats_index][values]
                    reqrate = rate.record_value_rate('datanode_'+values, stack_value, timestamp)
                    local_vars.append({'name': 'datanode_'+values.lower(), 'timestamp': timestamp, 'value': reqrate, 'check_type': check_type, 'chart_type': 'Rate'})

        for key in list(mon_values.keys()):
            if key is 'datanode_dfsused' or key is 'datanode_space_remaining':
                local_vars.append({'name': key.lower(), 'timestamp': timestamp, 'value': mon_values[key], 'check_type': check_type, 'reaction': reaction, 'chart_type': 'Rate'})
            else:
                local_vars.append({'name': key.lower(), 'timestamp': timestamp, 'value': mon_values[key], 'check_type': check_type, 'reaction': reaction})

        data_du_percent = mon_values['datanode_dfsused']*100/(mon_values['datanode_dfsused']+mon_values['datanode_space_remaining'])
        local_vars.append({'name': 'datanode_du_percent', 'timestamp': timestamp, 'value':data_du_percent, 'check_type': check_type, 'reaction': reaction, 'chart_type': 'Percent'})

        return local_vars
    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass

