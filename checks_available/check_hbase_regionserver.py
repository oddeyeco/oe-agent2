import lib.record_rate
import lib.commonclient
import lib.puylogger
import lib.getconfig
import lib.basecheck
# import datetime
import json


hbase_region_url = lib.getconfig.getparam('HBase-Region', 'jmx')
# cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_type = 'hbase'

class Check(lib.basecheck.CheckBase):

    def precheck(self):
        # local_vars = []
        try:
            stats_json = json.loads(lib.commonclient.httpget(__name__, hbase_region_url))
            stats_keys = stats_json['beans']
            node_rated_keys=('totalRequestCount','readRequestCount','writeRequestCount', 'Delete_num_ops', 'Mutate_num_ops', 'FlushTime_num_ops',
                             'GcTimeMillis','compactedCellsCount', 'majorCompactedCellsCount', 'compactedCellsSize', 'majorCompactedCellsSize',
                             'blockCacheHitCount', 'blockCacheMissCount', 'blockCacheEvictionCount')
            node_stuck_keys=('GcCount', 'HeapMemoryUsage', 'OpenFileDescriptorCount',
                             'blockCacheCount', 'blockCacheSize', 'blockCacheFreeSize', 'blockCacheExpressHitPercent', 'blockCountHitPercent',
                             'slowAppendCount', 'slowGetCount', 'slowPutCount', 'slowIncrementCount', 'slowDeleteCount')
            # rate=lib.record_rate.ValueRate()
            # timestamp = int(datetime.datetime.now().strftime("%s"))
    
            for stats_x in range(0, len(stats_keys)):
                for k, v in enumerate(('java.lang:type=GarbageCollector,name=ConcurrentMarkSweep', 'java.lang:type=GarbageCollector,name=ParNew')):
                    if v in stats_keys[stats_x]['name']:
                        if k is 0:
                            cms_key='hregion_heap_cms_lastgcinfo'
                            cms_value=stats_keys[stats_x]['LastGcInfo']['duration']
                            self.local_vars.append({'name': cms_key, 'timestamp': self.timestamp, 'value': cms_value, 'check_type': check_type})
                        if k is 1:
                            parnew_key='hregion_heap_parnew_lastgcinfo'
                            parnew_value=stats_keys[stats_x]['LastGcInfo']['duration']
                            self.local_vars.append({'name': parnew_key, 'timestamp': self.timestamp, 'value': parnew_value, 'check_type': check_type})
    
            for stats_x in range(0, len(stats_keys)):
                for k, v in enumerate(('java.lang:type=GarbageCollector,name=G1 Young Generation', 'java.lang:type=GarbageCollector,name=G1 Old Generation')):
                    if v in stats_keys[stats_x]['name']:
                        if k is 0:
                            g1_young_key='hregion_heap_g1_young_lastgcinfo'
                            g1_young_value=stats_keys[stats_x]['LastGcInfo']['duration']
                            self.local_vars.append({'name': g1_young_key, 'timestamp': self.timestamp, 'value': g1_young_value, 'check_type': check_type})
                        if k is 1:
                            if stats_keys[stats_x]['LastGcInfo'] is not None:
                                g1_old_key='hregion_heap_g1_old_lastgcinfo'
                                g1_old_value=stats_keys[stats_x]['LastGcInfo']['duration']
                                self.local_vars.append({'name': g1_old_key, 'timestamp': self.timestamp, 'value': g1_old_value, 'check_type': check_type})
                            else:
                                g1_old_key='hregion_heap_g1_old_lastgcinfo'
                                g1_old_value=0
                                self.local_vars.append({'name': g1_old_key, 'timestamp': self.timestamp, 'value': g1_old_value, 'check_type': check_type})
    
            for stats_index in range(0, len(stats_keys)):
                for values in node_rated_keys:
                    if values in stats_keys[stats_index]:
                        if values in node_rated_keys:
                            myvalue=stats_keys[stats_index][values]
                            values_rate=self.rate.record_value_rate('hregion_'+values, myvalue, self.timestamp)
                            if values_rate >= 0:
                                self.local_vars.append({'name': 'hregion_node_'+values.lower(), 'timestamp': self.timestamp, 'value': values_rate, 'check_type': check_type, 'chart_type': 'Rate'})
    
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
    
            # return  local_vars
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
