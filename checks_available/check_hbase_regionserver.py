import lib.record_rate
import lib.commonclient
import lib.puylogger
import lib.getconfig
import lib.basecheck
import json


hbase_region_url = lib.getconfig.getparam('HBase-Region', 'jmx')
check_type = 'hbase'


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            stats_json = json.loads(lib.commonclient.httpget(__name__, hbase_region_url))
            stats_keys = stats_json['beans']
            node_rated_keys = ('totalRequestCount', 'readRequestCount', 'writeRequestCount', 'Delete_num_ops', 'Mutate_num_ops', 'FlushTime_num_ops',
                                'GcTimeMillis', 'compactedCellsCount', 'majorCompactedCellsCount', 'compactedCellsSize', 'majorCompactedCellsSize')
            node_stuck_keys = ('GcCount', 'HeapMemoryUsage', 'OpenFileDescriptorCount',
                             'blockCacheSize', 'blockCacheExpressHitPercent', 'blockCountHitPercent',
                             'slowAppendCount', 'slowGetCount', 'slowPutCount', 'slowIncrementCount', 'slowDeleteCount',
                             'memStoreSize', 'regionCount', 'storeFileSize', 'storeFileCount', 'hlogFileCount', 'hlogFileSize', 'percentFilesLocal', 'blockCountHitPercent')
            zero_learn_keys = ('blockCacheFreeSize', 'blockCacheCount')
            zero_learn_keys_rated = ('blockCacheHitCount', 'blockCacheMissCount', 'blockCacheEvictionCount')
            hedged_reads = ('hedgedReads', 'hedgedReadWins')

            for stats_x in range(0, len(stats_keys)):
                if 'LastGcInfo' in stats_keys[stats_x] and stats_keys[stats_x]['LastGcInfo'] is not None:
                    if 'duration' in stats_keys[stats_x]['LastGcInfo']:
                        nam = stats_keys[stats_x]['Name'].replace('ConcurrentMarkSweep', 'cms').replace(' Generation', '').lower().replace(' ', '_')
                        vle = stats_keys[stats_x]['LastGcInfo']['duration']
                        self.local_vars.append({'name': 'hmaster_lastgcinfo', 'timestamp': self.timestamp, 'value': vle, 'check_type': check_type, 'extra_tag': {'gctype': nam}})
                        for o in ('CollectionCount', 'CollectionTime'):
                            vle = stats_keys[stats_x][o]
                            self.local_vars.append({'name': 'hmaster_gc_' + o.lower(), 'timestamp': self.timestamp, 'value': vle, 'check_type': check_type, 'reaction': -1, 'extra_tag': {'gctype': nam}})
            for stats_index in range(0, len(stats_keys)):
                for values in node_rated_keys:
                    if values in stats_keys[stats_index]:
                        if values in node_rated_keys:
                            myvalue = stats_keys[stats_index][values]
                            values_rate = self.rate.record_value_rate('hregion_'+values, myvalue, self.timestamp)
                            if values_rate >= 0:
                                self.local_vars.append({'name': 'hregion_node_'+values.lower(), 'timestamp': self.timestamp, 'value': values_rate, 'check_type': check_type, 'chart_type': 'Rate'})
                for values in zero_learn_keys_rated:
                    if values in stats_keys[stats_index]:
                        if values in node_rated_keys:
                            myvalue = stats_keys[stats_index][values]
                            values_rate = self.rate.record_value_rate('hregion_'+values, myvalue, self.timestamp)
                            if values_rate >= 0:
                                self.local_vars.append({'name': 'hregion_node_'+values.lower(), 'timestamp': self.timestamp, 'value': values_rate, 'check_type': check_type, 'chart_type': 'Rate', 'reaction': -3})
                for values in zero_learn_keys:
                    if values in stats_keys[stats_index]:
                        self.local_vars.append({'name': 'hregion_node_' + values.lower(), 'timestamp': self.timestamp, 'value': stats_keys[stats_index][values], 'check_type': check_type, 'reaction': -3})
                for values in hedged_reads:
                    if values in stats_keys[stats_index]:
                        if stats_keys[stats_index][values] > 0:
                            self.local_vars.append({'name': 'hregion_node_' + values.lower(), 'timestamp': self.timestamp, 'value': stats_keys[stats_index][values], 'check_type': check_type})
                for values in node_stuck_keys:
                    if values in stats_keys[stats_index]:
                        if values == 'HeapMemoryUsage':
                            heap_metrics=('max', 'init', 'committed', 'used')
                            for heap_values in heap_metrics:
                                self.local_vars.append({'name': 'hregion_heap_'+heap_values.lower(), 'timestamp': self.timestamp, 'value': stats_keys[stats_index][values][heap_values], 'check_type': check_type})
                        elif values == 'GcCount':
                            self.local_vars.append({'name': 'hregion_node_' + values.lower(), 'timestamp': self.timestamp, 'value': stats_keys[stats_index][values], 'check_type': check_type, 'reaction': -3, 'chart_type': 'Counter'})
                        elif values.startswith('slow'):
                            self.local_vars.append({'name': 'hregion_node_' + values.lower(), 'timestamp': self.timestamp, 'value': stats_keys[stats_index][values], 'check_type': check_type, 'reaction': -1, 'chart_type': 'Counter'})
                        else:
                            self.local_vars.append({'name': 'hregion_node_'+values.lower(), 'timestamp': self.timestamp, 'value': stats_keys[stats_index][values], 'check_type': check_type})
    
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
