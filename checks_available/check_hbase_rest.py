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
                if 'LastGcInfo' in stats_keys[stats_x] and stats_keys[stats_x]['LastGcInfo'] is not None:
                    if 'duration' in stats_keys[stats_x]['LastGcInfo']:
                        nam = stats_keys[stats_x]['Name'].replace('ConcurrentMarkSweep', 'cms').replace(' Generation', '').lower().replace(' ', '_')
                        vle = stats_keys[stats_x]['LastGcInfo']['duration']
                        self.local_vars.append({'name': 'hrest_lastgcinfo', 'timestamp': self.timestamp, 'value': vle, 'check_type': check_type, 'extra_tag': {'gctype': nam}})
                        for o in ('CollectionCount', 'CollectionTime'):
                            vle = stats_keys[stats_x][o]
                            self.local_vars.append({'name': 'hrest_gc_' + o.lower(), 'timestamp': self.timestamp, 'value': vle, 'check_type': check_type, 'reaction': -1, 'extra_tag': {'gctype': nam}})

            thread_metrics = ('TotalStartedThreadCount', 'PeakThreadCount', 'ThreadCount', 'DaemonThreadCount')
            for index in range(0, len(stats_keys)):
                if stats_keys[index]['name'] == 'java.lang:type=Threading':
                    for thread_metric in thread_metrics:
                        self.local_vars.append({'name': 'hrest_' + thread_metric.lower(), 'timestamp': self.timestamp, 'value': stats_keys[index][thread_metric], 'check_type': check_type})
                if stats_keys[index]['name'] == 'java.lang:type=Memory':
                    heap_metrics = ('max', 'init', 'committed', 'used')
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
