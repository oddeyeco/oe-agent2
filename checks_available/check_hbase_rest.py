import lib.record_rate
import lib.commonclient
import lib.puylogger
import lib.getconfig
import lib.basecheck
import json

hbase_rest_url = lib.getconfig.getparam('HBase-Rest', 'jmx')
check_type = 'hbase'


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            stats_json = json.loads(lib.commonclient.httpget(__name__, hbase_rest_url))
            stats_keys = stats_json['beans']
            for stats_x in range(0, len(stats_keys)):
                for k, v in enumerate(('java.lang:type=GarbageCollector,name=ConcurrentMarkSweep', 'java.lang:type=GarbageCollector,name=ParNew')):
                    if v in stats_keys[stats_x]['name']:
                        if k is 0:
                            cms_key = 'hrest_cms_lastgcinfo'
                            cms_value = stats_keys[stats_x]['LastGcInfo']['duration']
                            self.local_vars.append({'name': cms_key, 'timestamp': self.timestamp, 'value': cms_value, 'check_type': check_type})
                        if k is 1:
                            parnew_key = 'hrest_parnew_lastgcinfo'
                            parnew_value = stats_keys[stats_x]['LastGcInfo']['duration']
                            self.local_vars.append({'name': parnew_key, 'timestamp': self.timestamp, 'value': parnew_value, 'check_type': check_type})

            for stats_x in range(0, len(stats_keys)):
                for k, v in enumerate(('java.lang:type=GarbageCollector,name=G1 Young Generation', 'java.lang:type=GarbageCollector,name=G1 Old Generation')):
                    if v in stats_keys[stats_x]['name']:
                        if k is 0:
                            g1_young_key = 'hrest_g1_young_lastgcinfo'
                            g1_young_value = stats_keys[stats_x]['LastGcInfo']['duration']
                            self.local_vars.append({'name': g1_young_key, 'timestamp': self.timestamp, 'value': g1_young_value, 'check_type': check_type})
                        if k is 1:
                            if stats_keys[stats_x]['LastGcInfo'] is not None:
                                g1_old_key = 'hrest_g1_old_lastgcinfo'
                                g1_old_value = stats_keys[stats_x]['LastGcInfo']['duration']
                                self.local_vars.append({'name': g1_old_key, 'timestamp': self.timestamp, 'value': g1_old_value, 'check_type': check_type})
                            else:
                                g1_old_key = 'hrest_g1_old_lastgcinfo'
                                g1_old_value = 0
                                self.local_vars.append({'name': g1_old_key, 'timestamp': self.timestamp, 'value': g1_old_value, 'check_type': check_type})

            thread_metrics = ('TotalStartedThreadCount', 'PeakThreadCount', 'ThreadCount', 'DaemonThreadCount')
            for index in range(0, len(stats_keys)):
                if stats_keys[index]['name'] == 'java.lang:type=Threading':
                    for thread_metric in thread_metrics:
                        self.local_vars.append({'name': 'hrest_' + thread_metric.lower(), 'timestamp': self.timestamp, 'value': stats_keys[index][thread_metric], 'check_type': check_type})
                if stats_keys[index]['name'] == 'java.lang:type=Memory':
                    heap_metrics=('max', 'init', 'committed', 'used')
                    for heap_value in heap_metrics:
                        self.local_vars.append({'name': 'hrest_heap_' + heap_value, 'timestamp': self.timestamp, 'value': stats_keys[index]['HeapMemoryUsage'][heap_value], 'check_type': check_type})
                if stats_keys[index]['name'] == 'Hadoop:service=HBase,name=REST':
                    hrmetrics = ('PauseTimeWithGc_99th_percentile', 'PauseTimeWithGc_90th_percentile',
                                 'PauseTimeWithoutGc_90th_percentile', 'PauseTimeWithoutGc_99th_percentile')
                    hrmetrics_rated = ('requests', 'successfulDelete', 'successfulGet', 'successfulPut', 'successfulScanCount',
                                       'failedDelete', 'failedGet', 'failedPut', 'failedScanCount')
                    for hrmetric in hrmetrics:
                        self.local_vars.append({'name': 'hrest_' + hrmetric.lower(), 'timestamp': self.timestamp, 'value': stats_keys[index][hrmetric], 'check_type': check_type})
                    for hrmetric_rated in hrmetrics_rated:
                        bolor = self.rate.record_value_rate('hrest_' + hrmetric_rated, stats_keys[index][hrmetric_rated], self.timestamp)
                        self.local_vars.append({'name': 'hrest_' + hrmetric_rated.lower(), 'timestamp': self.timestamp, 'value': bolor, 'check_type': check_type, 'chart_type': 'Rate'})
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass

