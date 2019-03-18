import lib.record_rate
import lib.getconfig
import lib.commonclient
import lib.puylogger
import lib.basecheck
import json

hadoop_namenode_url = lib.getconfig.getparam('Hadoop-NameNode', 'jmx')
check_type = 'hdfs'


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            hadoop_namenode_stats = json.loads(lib.commonclient.httpget(__name__, hadoop_namenode_url))
            stats_keys = hadoop_namenode_stats['beans']
            node_stack_keys = ('CapacityTotal', 'CapacityUsed', 'BlocksTotal', 'MissingBlocks', 'CorruptBlocks', 'UnderReplicatedBlocks',
                               'PendingReplicationBlocks', 'ScheduledReplicationBlocks', 'BlockCapacity',
                               'NonDfsUsedSpace', 'CapacityRemaining', 'PercentRemaining', 'OpenFileDescriptorCount', 'NumStaleDataNodes', 'NumStaleStorages',
                               'NumLiveDataNodes', 'NumDeadDataNodes', 'NumDecomLiveDataNodes', 'NumDecomDeadDataNodes', 'NumDecommissioningDataNodes')
            node_rated_keys = ('CreateFileOps', 'GetBlockLocations', 'FilesRenamed', 'GetListingOps', 'DeleteFileOps', 'FilesDeleted',
                               'FileInfoOps', 'AddBlockOps', 'TransactionsNumOps', 'ReceivedBytes', 'SentBytes')
            mon_values = {}

            for stats_index in range(0, len(stats_keys)):

                for v in ('NonHeapMemoryUsage', 'HeapMemoryUsage'):
                    if v in stats_keys[stats_index]:
                        heap_metrics = ('max', 'init', 'committed', 'used')
                        name = v.replace('Node', '').replace('Usage', '').replace('Memory', '').lower()
                        for heap_values in heap_metrics:
                            mon_values.update({'namenode_' + name + '_' + heap_values: stats_keys[stats_index][v][heap_values]})

                if 'LastGcInfo' in stats_keys[stats_index] and stats_keys[stats_index]['LastGcInfo'] is not None:
                    if 'duration' in stats_keys[stats_index]['LastGcInfo']:
                        nam = stats_keys[stats_index]['Name'].replace('ConcurrentMarkSweep', 'cms').replace(' Generation', '').lower().replace(' ', '_')
                        vle = stats_keys[stats_index]['LastGcInfo']['duration']
                        self.local_vars.append({'name': 'namenode_lastgcinfo', 'timestamp': self.timestamp, 'value': vle, 'check_type': check_type, 'extra_tag': {'gctype': nam}})
                        for o in ('CollectionCount', 'CollectionTime'):
                            vle = stats_keys[stats_index][o]
                            self.local_vars.append({'name': 'namenode_gc_' + o.lower(), 'timestamp': self.timestamp, 'value': vle, 'check_type': check_type, 'reaction': -1, 'extra_tag': {'gctype': nam}})

                for values in node_stack_keys:
                    if values in stats_keys[stats_index]:
                        mon_values.update({'namenode_' + values.lower(): stats_keys[stats_index][values]})
                for values in node_rated_keys:
                    if values in stats_keys[stats_index]:
                        stack_value = stats_keys[stats_index][values]
                        reqrate = self.rate.record_value_rate('namenode_'+values, stack_value, self.timestamp)
                        self.local_vars.append({'name': 'namenode_'+values.lower(), 'timestamp': self.timestamp, 'value': reqrate, 'check_type': check_type, 'chart_type': 'Rate'})

            for key in list(mon_values.keys()):
                self.local_vars.append({'name': key.lower(), 'timestamp': self.timestamp, 'value': mon_values[key], 'check_type': check_type})
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
