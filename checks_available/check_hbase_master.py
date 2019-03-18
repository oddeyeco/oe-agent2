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
            node_rated_keys = ('clusterRequests', 'GcTimeMillis')
            node_stuck_keys = ('GcCount', 'HeapMemoryUsage', 'numRegionServers', 'numDeadRegionServers',
                               'ritOldestAge', 'ritCountOverThreshold', 'ritCount', 'averageLoad', 'numRegionServers', 'numDeadRegionServers')
            exceptions = ('exceptions.RegionMovedException', 'exceptions.multiResponseTooLarge', 'exceptions.RegionTooBusyException',
                          'exceptions.FailedSanityCheckException', 'exceptions.UnknownScannerException',
                          'exceptions.OutOfOrderScannerNextException', 'exceptions')

            for stats_x in range(0, len(stats_keys)):
                if 'LastGcInfo' in stats_keys[stats_x] and stats_keys[stats_x]['LastGcInfo'] is not None:
                    if 'duration' in stats_keys[stats_x]['LastGcInfo']:
                        nam = stats_keys[stats_x]['Name'].replace('ConcurrentMarkSweep', 'cms').replace(' Generation', '').lower().replace(' ', '_')
                        vle = stats_keys[stats_x]['LastGcInfo']['duration']
                        self.local_vars.append({'name': 'hmaster_lastgcinfo', 'timestamp': self.timestamp, 'value': vle, 'check_type': check_type, 'extra_tag': {'gctype': nam}})
                        for o in ('CollectionCount', 'CollectionTime'):
                            vle = stats_keys[stats_x][o]
                            self.local_vars.append({'name': 'hmaster_gc_' + o.lower(), 'timestamp': self.timestamp, 'value': vle, 'check_type': check_type, 'reaction': -1, 'extra_tag': {'gctype': nam}})

            for stats_x in range(0, len(stats_keys)):
                for values in node_rated_keys:
                    if values in stats_keys[stats_x]:
                        if values in node_rated_keys:
                            myvalue = stats_keys[stats_x][values]
                            values_rate = self.rate.record_value_rate('hmaster_'+values, myvalue, self.timestamp)
                            if values_rate >= 0:
                                self.local_vars.append({'name': 'hmaster_node_' + values.lower(), 'timestamp': self.timestamp, 'value': values_rate, 'check_type': check_type, 'chart_type': 'Rate'})

                for values in node_stuck_keys:
                    if values in stats_keys[stats_x]:
                        if values == 'HeapMemoryUsage':
                            heap_metrics = ('max', 'init', 'committed', 'used')
                            for heap_values in heap_metrics:
                                self.local_vars.append({'name': 'hmaster_heap_' + heap_values.lower(), 'timestamp': self.timestamp, 'value': stats_keys[stats_x][values][heap_values], 'check_type': check_type})
                        elif values == 'GcCount':
                            self.local_vars.append({'name': 'hmaster_node_' + values.lower(), 'timestamp': self.timestamp, 'value': stats_keys[stats_x][values], 'check_type': check_type, 'reaction': -3})
                        else:
                            self.local_vars.append({'name': 'hmaster_node_' + values.lower(), 'timestamp': self.timestamp, 'value': stats_keys[stats_x][values], 'check_type': check_type})

                for values in exceptions:
                    if values in stats_keys[stats_x]:
                        vv = values.lower().replace('.', '_').replace('exceptions', '').replace('exception', '')
                        self.local_vars.append({'name': 'hmaster_exceptions' + vv, 'timestamp': self.timestamp, 'value': stats_keys[stats_x][values], 'check_type': check_type})

        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
