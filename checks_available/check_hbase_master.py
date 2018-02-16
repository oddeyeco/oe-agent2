import lib.record_rate
import lib.commonclient
import lib.getconfig
import lib.puylogger
import lib.basecheck
import json


hbase_master_url = lib.getconfig.getparam('HBase-Master', 'jmx')
check_type = 'hbase'

class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            stats_json = json.loads(lib.commonclient.httpget(__name__, hbase_master_url))
            stats_keys = stats_json['beans']
            node_rated_keys = ('clusterRequests','GcTimeMillis')
            node_stuck_keys = ('GcCount','HeapMemoryUsage', 'numRegionServers', 'numDeadRegionServers',
                               'ritOldestAge', 'ritCountOverThreshold', 'ritCount', 'averageLoad', 'numRegionServers', 'numDeadRegionServers')
            exceptions = ('exceptions.RegionMovedException', 'exceptions.multiResponseTooLarge', 'exceptions.RegionTooBusyException',
                          'exceptions.FailedSanityCheckException', 'exceptions.UnknownScannerException',
                          'exceptions.OutOfOrderScannerNextException', 'exceptions')
            for stats_x in range(0, len(stats_keys)):
                for k, v in enumerate(('java.lang:type=GarbageCollector,name=ConcurrentMarkSweep', 'java.lang:type=GarbageCollector,name=ParNew')):
                    if v in stats_keys[stats_x]['name']:
                        if k is 0:
                            cms_key = 'hmaster_heap_cms_lastgcInfo'
                            cms_value = stats_keys[stats_x]['LastGcInfo']['duration']
                            self.local_vars.append({'name': cms_key, 'timestamp': self.timestamp, 'value': cms_value, 'check_type': check_type})
                        if k is 1:
                            parnew_key = 'hmaster_heap_parnew_lastgcinfo'
                            parnew_value = stats_keys[stats_x]['LastGcInfo']['duration']
                            self.local_vars.append({'name': parnew_key, 'timestamp': self.timestamp, 'value': parnew_value, 'check_type': check_type})
    
            for stats_x in range(0, len(stats_keys)):
                for k, v in enumerate(('java.lang:type=GarbageCollector,name=G1 Young Generation', 'java.lang:type=GarbageCollector,name=G1 Old Generation')):
                    if v in stats_keys[stats_x]['name']:
                        if k is 0:
                            g1_young_key = 'hmaster_heap_g1_young_lastgcInfo'
                            g1_young_value = stats_keys[stats_x]['LastGcInfo']['duration']
                            self.local_vars.append({'name': g1_young_key, 'timestamp': self.timestamp, 'value': g1_young_value, 'check_type': check_type})
    
                        if k is 1:
                            if stats_keys[stats_x]['LastGcInfo'] is not None:
                                g1_old_key = 'hmaster_heap_g1_old_lastgcInfo'
                                g1_old_value = stats_keys[stats_x]['LastGcInfo']['duration']
                                self.local_vars.append({'name': g1_old_key, 'timestamp': self.timestamp, 'value': g1_old_value, 'check_type': check_type})
                            else:
                                g1_old_key = 'hmaster_heap_g1_old_lastgcinfo'
                                g1_old_value = 0
                                self.local_vars.append({'name': g1_old_key, 'timestamp': self.timestamp, 'value': g1_old_value, 'check_type': check_type})
    
            for stats_index in range(0, len(stats_keys)):
                for values in node_rated_keys:
                    if values in stats_keys[stats_index]:
                        if values in node_rated_keys:
                            myvalue = stats_keys[stats_index][values]
                            values_rate = self.rate.record_value_rate('hmaster_'+values, myvalue, self.timestamp)
                            if values_rate >= 0:
                                self.local_vars.append({'name': 'hmaster_node_' + values.lower(), 'timestamp': self.timestamp, 'value': values_rate, 'check_type': check_type, 'chart_type': 'Rate'})

                for values in node_stuck_keys:
                    if values in stats_keys[stats_index]:
                        if values == 'HeapMemoryUsage':
                            heap_metrics = ('max', 'init', 'committed', 'used')
                            for heap_values in heap_metrics:
                                self.local_vars.append({'name': 'hmaster_heap_' + heap_values.lower(), 'timestamp': self.timestamp, 'value': stats_keys[stats_index][values][heap_values], 'check_type': check_type})
                        elif values == 'GcCount':
                            self.local_vars.append({'name': 'hmaster_node_' + values.lower(), 'timestamp': self.timestamp, 'value': stats_keys[stats_index][values], 'check_type': check_type, 'reaction': -3})
                        else:
                            self.local_vars.append({'name': 'hmaster_node_' + values.lower(), 'timestamp': self.timestamp, 'value': stats_keys[stats_index][values], 'check_type': check_type})

                for values in exceptions:
                    if values in stats_keys[stats_index]:
                        vv = values.lower().replace('.', '_').replace('exceptions', '').replace('exception', '')
                        self.local_vars.append({'name': 'hmaster_exceptions' + vv, 'timestamp': self.timestamp, 'value': stats_keys[stats_index][values], 'check_type': check_type})


        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
