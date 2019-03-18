import lib.record_rate
import lib.commonclient
import lib.getconfig
import lib.puylogger
import lib.basecheck
import json

hadoop_datanode_url = lib.getconfig.getparam('Hadoop-Datanode', 'jmx')
check_type = 'hdfs'
warn_level = 20


class Check(lib.basecheck.CheckBase):

    def precheck(self):
    
        try:
            hadoop_datanode_stats = json.loads(lib.commonclient.httpget(__name__, hadoop_datanode_url))
            stats_keys = hadoop_datanode_stats['beans']
            node_stack_keys = ('NonHeapMemoryUsage', 'HeapMemoryUsage', 'Capacity', 'DfsUsed', 'Remaining', 'OpenFileDescriptorCount')
            node_rated_keys = ('BytesRead', 'BytesWritten', 'TotalReadTime', 'TotalWriteTime')
            mon_values = {}

            for stats_index in range(0, len(stats_keys)):
                for values in node_stack_keys:
                    if values in stats_keys[stats_index]:
                        if values == 'HeapMemoryUsage':
                            heap_metrics = ('max', 'init', 'committed', 'used')
                            for heap_values in heap_metrics:
                                mon_values.update({'datanode_heap_'+heap_values: stats_keys[stats_index][values][heap_values]})
                        if values == 'NonHeapMemoryUsage':
                            heap_metrics = ('max', 'init', 'committed', 'used')
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

                if 'LastGcInfo' in stats_keys[stats_index] and stats_keys[stats_index]['LastGcInfo'] is not None:
                    if 'duration' in stats_keys[stats_index]['LastGcInfo']:
                        nam = stats_keys[stats_index]['Name'].replace('ConcurrentMarkSweep', 'cms').replace(' Generation', '').lower().replace(' ', '_')
                        vle = stats_keys[stats_index]['LastGcInfo']['duration']
                        self.local_vars.append({'name': 'datanode_lastgcinfo', 'timestamp': self.timestamp, 'value': vle, 'check_type': check_type, 'extra_tag': {'gctype': nam}})
                        for o in ('CollectionCount', 'CollectionTime'):
                            vle = stats_keys[stats_index][o]
                            self.local_vars.append({'name': 'datanode_gc_' + o.lower(), 'timestamp': self.timestamp, 'value': vle, 'check_type': check_type, 'reaction': -1, 'extra_tag': {'gctype': nam}})

                for values in node_rated_keys:
                    if values in stats_keys[stats_index]:
                        stack_value = stats_keys[stats_index][values]
                        reqrate = self.rate.record_value_rate('datanode_'+values, stack_value, self.timestamp)
                        self.local_vars.append({'name': 'datanode_'+values.lower(), 'timestamp': self.timestamp, 'value': reqrate, 'check_type': check_type, 'chart_type': 'Rate'})

            for key in list(mon_values.keys()):
                if key is 'datanode_dfsused' or key is 'datanode_space_remaining':
                    self.local_vars.append({'name': key.lower(), 'timestamp': self.timestamp, 'value': mon_values[key], 'check_type': check_type, 'reaction': -3, 'chart_type': 'Rate'})
                else:
                    self.local_vars.append({'name': key.lower(), 'timestamp': self.timestamp, 'value': mon_values[key], 'check_type': check_type, 'reaction': -3})

            data_du_percent = mon_values['datanode_dfsused']*100/(mon_values['datanode_dfsused'] + mon_values['datanode_space_remaining'])
            self.local_vars.append({'name': 'datanode_du_percent', 'timestamp': self.timestamp, 'value': data_du_percent, 'check_type': check_type, 'reaction': -3, 'chart_type': 'Percent'})
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
