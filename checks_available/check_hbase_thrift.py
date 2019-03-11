import lib.record_rate
import lib.commonclient
import lib.puylogger
import lib.getconfig
import lib.basecheck
import json

hbase_thrift_url = lib.getconfig.getparam('HBase-Thrift', 'jmx')
check_type = 'hbase'


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            stats_json = json.loads(lib.commonclient.httpget(__name__, hbase_thrift_url))
            stats_keys = stats_json['beans']
            for stats_x in range(0, len(stats_keys)):
                for k, v in enumerate(('java.lang:type=GarbageCollector,name=ConcurrentMarkSweep', 'java.lang:type=GarbageCollector,name=ParNew')):
                    if v in stats_keys[stats_x]['name']:
                        if k is 0:
                            if stats_keys[stats_x]['LastGcInfo'] is not None:
                                cms_key = 'hthrift_cms_lastgcinfo'
                                cms_value = stats_keys[stats_x]['LastGcInfo']['duration']
                                self.local_vars.append({'name': cms_key, 'timestamp': self.timestamp, 'value': cms_value, 'check_type': check_type})
                            else:
                                self.local_vars.append({'name': 'hthrift_cms_lastgcinfo', 'timestamp': self.timestamp, 'value': 0, 'check_type': check_type})
                        if k is 1:
                            if stats_keys[stats_x]['LastGcInfo'] is not None:
                                parnew_key = 'hthrift_parnew_lastgcinfo'
                                parnew_value = stats_keys[stats_x]['LastGcInfo']['duration']
                                self.local_vars.append({'name': parnew_key, 'timestamp': self.timestamp, 'value': parnew_value, 'check_type': check_type})
                            else:
                                self.local_vars.append({'name': 'hthrift_parnew_lastgcinfo', 'timestamp': self.timestamp, 'value': 0, 'check_type': check_type})

            for stats_x in range(0, len(stats_keys)):
                for k, v in enumerate(('java.lang:type=GarbageCollector,name=G1 Young Generation', 'java.lang:type=GarbageCollector,name=G1 Old Generation')):
                    if v in stats_keys[stats_x]['name']:
                        if k is 0:
                            if stats_keys[stats_x]['LastGcInfo'] is not None:
                                g1_young_key = 'hthrift_g1_young_lastgcinfo'
                                g1_young_value = stats_keys[stats_x]['LastGcInfo']['duration']
                                self.local_vars.append({'name': g1_young_key, 'timestamp': self.timestamp, 'value': g1_young_value, 'check_type': check_type})
                            else:
                                self.local_vars.append({'name': 'hthrift_g1_old_lastgcinfo', 'timestamp': self.timestamp, 'value': 0, 'check_type': check_type})
                        if k is 1:
                            if stats_keys[stats_x]['LastGcInfo'] is not None:
                                g1_old_key = 'hthrift_g1_old_lastgcinfo'
                                g1_old_value = stats_keys[stats_x]['LastGcInfo']['duration']
                                self.local_vars.append({'name': g1_old_key, 'timestamp': self.timestamp, 'value': g1_old_value, 'check_type': check_type})
                            else:
                                self.local_vars.append({'name': 'hthrift_g1_old_lastgcinfo', 'timestamp': self.timestamp, 'value': 0, 'check_type': check_type})

            thread_metrics = ('TotalStartedThreadCount', 'PeakThreadCount', 'ThreadCount', 'DaemonThreadCount')
            for index in range(0, len(stats_keys)):
                if stats_keys[index]['name'] == 'java.lang:type=Threading':
                    for thread_metric in thread_metrics:
                        self.local_vars.append({'name': 'hthrift_' + thread_metric.lower(), 'timestamp': self.timestamp, 'value': stats_keys[index][thread_metric], 'check_type': check_type})
                if stats_keys[index]['name'] == 'java.lang:type=Memory':
                    heap_metrics=('max', 'init', 'committed', 'used')
                    for heap_value in heap_metrics:
                        self.local_vars.append({'name': 'hthrift_heap_' + heap_value, 'timestamp': self.timestamp, 'value': stats_keys[index]['HeapMemoryUsage'][heap_value], 'check_type': check_type})

                if stats_keys[index]['name'] == 'Hadoop:service=HBase,name=Thrift,sub=ThriftOne':
                    hrmetrics = ('PauseTimeWithGc_99th_percentile', 'PauseTimeWithGc_90th_percentile',
                                 'PauseTimeWithoutGc_90th_percentile', 'PauseTimeWithoutGc_99th_percentile', 'callQueueLen', 'TimeInQueue_num_ops')
                    hrmetrics_rated = ('BatchMutate_num_ops', 'ThriftCall_num_ops', 'SlowThriftCall_num_ops', 'BatchGet_num_ops', )
                    for hrmetric in hrmetrics:
                        self.local_vars.append({'name': 'hthrift_' + hrmetric.lower(), 'timestamp': self.timestamp, 'value': stats_keys[index][hrmetric], 'check_type': check_type, 'extra_tag': {'thrift_queue': 'one'}})

                    for hrmetric_rated in hrmetrics_rated:
                        bolor = self.rate.record_value_rate('hthrift_one' + hrmetric_rated, stats_keys[index][hrmetric_rated], self.timestamp)
                        self.local_vars.append({'name': 'hthrift_' + hrmetric_rated.replace('_num_ops', '').lower(), 'timestamp': self.timestamp, 'value': bolor, 'check_type': check_type, 'chart_type': 'Rate', 'extra_tag': {'thrift_queue': 'one'}})

                if stats_keys[index]['name'] == 'Hadoop:service=HBase,name=Thrift,sub=ThriftTwo':
                    hrmetrics = ('PauseTimeWithGc_99th_percentile', 'PauseTimeWithGc_90th_percentile',
                                 'PauseTimeWithoutGc_90th_percentile', 'PauseTimeWithoutGc_99th_percentile', 'callQueueLen', 'TimeInQueue_num_ops')
                    hrmetrics_rated = ('BatchMutate_num_ops', 'ThriftCall_num_ops', 'SlowThriftCall_num_ops', 'BatchGet_num_ops', )
                    for hrmetric in hrmetrics:
                        self.local_vars.append({'name': 'hthrift_' + hrmetric.lower(), 'timestamp': self.timestamp, 'value': stats_keys[index][hrmetric], 'check_type': check_type, 'extra_tag': {'thrift_queue': 'two'}})

                    for hrmetric_rated in hrmetrics_rated:
                        bolor = self.rate.record_value_rate('hthrift_two' + hrmetric_rated, stats_keys[index][hrmetric_rated], self.timestamp)
                        self.local_vars.append({'name': 'hthrift_' + hrmetric_rated.replace('_num_ops', '').lower(), 'timestamp': self.timestamp, 'value': bolor, 'check_type': check_type, 'chart_type': 'Rate', 'extra_tag': {'thrift_queue': 'two'}})
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass

