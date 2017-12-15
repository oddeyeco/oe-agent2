import lib.record_rate
import lib.pushdata
import lib.puylogger
import lib.jolostart
import lib.commonclient
import lib.getconfig
import lib.basecheck
import json

hrest_url = lib.getconfig.getparam('HBase-Rest', 'url')
java = lib.getconfig.getparam('HBase-Rest', 'java')
juser = lib.getconfig.getparam('HBase-Rest', 'user')
jclass = lib.getconfig.getparam('HBase-Rest', 'class')
check_type = 'hbase'
reaction = -3

lib.jolostart.do_joloikia(java, juser, jclass, hrest_url)


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        
        try:
            data_dict = json.loads(lib.commonclient.httpget(__name__, hrest_url + '/java.lang:type=GarbageCollector,name=*'))
            ConcurrentMarkSweep = 'java.lang:name=ConcurrentMarkSweep,type=GarbageCollector'
            G1Gc = 'java.lang:name=G1 Young Generation,type=GarbageCollector'
    
            if ConcurrentMarkSweep in data_dict['value']:
                CMS = True
                G1 = False
            elif G1Gc in data_dict['value']:
                CMS = False
                G1 = True
            else:
                CMS = False
                G1 = False
    
            heam_mem = 'java.lang:type=Memory'
            jolo_json = json.loads(lib.commonclient.httpget(__name__, hrest_url + '/' + heam_mem))
            jolo_keys = jolo_json['value']
            metr_name = ('used', 'committed', 'max')
            heap_type = ('NonHeapMemoryUsage', 'HeapMemoryUsage')
            for heap in heap_type:
                for metr in metr_name:
                    if heap == 'NonHeapMemoryUsage':
                        key = 'hrest_nonheap_' + metr
                        mon_values = jolo_keys[heap][metr]
                        if metr == 'used':
                            self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': mon_values, 'check_type': check_type})
                        else:
                            self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': mon_values, 'check_type': check_type, 'reaction': reaction})
                    else:
                        key = 'hrest_heap_' + metr
                        mon_values = jolo_keys[heap][metr]
                        if metr == 'used':
                            self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': mon_values, 'check_type': check_type})
                        else:
                            self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': mon_values, 'check_type': check_type, 'reaction': reaction})
            if CMS is True:
                collector = ('java.lang:name=ParNew,type=GarbageCollector', 'java.lang:name=ConcurrentMarkSweep,type=GarbageCollector')
                for coltype in collector:
                    beans = json.loads(lib.commonclient.httpget(__name__, hrest_url + '/' + coltype))
                    if beans['value']['LastGcInfo']:
                        LastGcInfo = beans['value']['LastGcInfo']['duration']
                    CollectionCount = beans['value']['CollectionCount']
                    CollectionTime = beans['value']['CollectionTime']
    
                    def push_metrics(preffix):
                        CollectionTime_rate = self.rate.record_value_rate('hrest_' + preffix + '_collection_time', CollectionTime, self.timestamp)
                        if 'LastGcInfo' in locals():
                            self.local_vars.append({'name': 'hrest_' + preffix + '_lastgcinfo', 'timestamp': self.timestamp, 'value': LastGcInfo, 'check_type': check_type})
                        self.local_vars.append({'name': 'hrest_' + preffix + '_collection_count', 'timestamp': self.timestamp, 'value': CollectionCount, 'check_type': check_type})
                        self.local_vars.append({'name': 'hrest_' + preffix + '_collection_time', 'timestamp': self.timestamp, 'value': CollectionTime_rate, 'check_type': check_type, 'chart_type': 'Rate'})
    
                    if coltype == 'java.lang:name=ConcurrentMarkSweep,type=GarbageCollector':
                        push_metrics(preffix='cms')
                    if coltype == 'java.lang:name=ParNew,type=GarbageCollector':
                        push_metrics(preffix='parnew')
    
            if G1 is True:
                gc_g1 = ('/java.lang:name=G1%20Old%20Generation,type=GarbageCollector', '/java.lang:name=G1%20Young%20Generation,type=GarbageCollector')
    
                def check_null(value):
                    if value is None:
                        value = 0
                        return value
                    else:
                        return value
    
                for k, v in enumerate(gc_g1):
                    j = json.loads(lib.commonclient.httpget(__name__, hrest_url + v))
                    name = 'LastGcInfo'
                    if k is 0:
                        try:
                            value = j['value'][name]['duration']
                            v = check_null(value)
                        except:
                            v = 0
                            pass
                        m_name = 'hrest_g1_old_lastgcinfo'
                    if k is 1:
                        value = j['value'][name]['duration']
                        v = check_null(value)
                        m_name = 'hrest_g1_young_lastgcinfo'
                    self.local_vars.append({'name': m_name, 'timestamp': self.timestamp, 'value': v, 'check_type': check_type})
    
                metr_keys = ('CollectionTime', 'CollectionCount')
                for k, v in enumerate(gc_g1):
                    j = json.loads(lib.commonclient.httpget(__name__, hrest_url + v))
                    if k is 0:
                        type = '_old_'
                    if k is 1:
                        type = '_young_'
                    for ky, vl in enumerate(metr_keys):
                        if ky is 0:
                            value = j['value'][vl]
                            v = check_null(value)
                            rate_key = vl + type
                            CollectionTime_rate = self.rate.record_value_rate('hrest_' + rate_key, v, self.timestamp)
                            self.local_vars.append({'name': 'hrest_g1' + type + vl, 'timestamp': self.timestamp, 'value': CollectionTime_rate, 'check_type': check_type, 'chart_type': 'Rate'})
                        if ky is 1:
                            value = j['value'][vl]
                            v = check_null(value)
                            self.local_vars.append({'name': 'hrest_g1' + type + vl, 'timestamp': self.timestamp, 'value': v, 'check_type': check_type})
            jolo_threads = 'java.lang:type=Threading'
            jolo_tjson = json.loads(lib.commonclient.httpget(__name__, hrest_url + '/' + jolo_threads))
            thread_metrics = ('TotalStartedThreadCount', 'PeakThreadCount', 'ThreadCount', 'DaemonThreadCount')
            for thread_metric in thread_metrics:
                name = 'hrest_' + thread_metric.lower()
                vlor = jolo_tjson['value'][thread_metric]
                self.local_vars.append({'name': name, 'timestamp': self.timestamp, 'value': vlor, 'check_type': check_type})
    
            jolo_thrift = 'Hadoop:service=HBase,name=REST'
            jolo_tjson = json.loads(lib.commonclient.httpget(__name__, hrest_url + '/' + jolo_thrift))
            hrmetrics = ('requests', 'PauseTimeWithGc_99th_percentile', 'PauseTimeWithGc_90th_percentile',
                         'PauseTimeWithoutGc_90th_percentile', 'PauseTimeWithoutGc_99th_percentile')
    
            hrmetrics_rated = ('successfulDelete', 'successfulGet', 'successfulPut', 'successfulScanCount',
                         'failedDelete', 'failedGet', 'failedPut', 'failedScanCount')
            for thread_metric in hrmetrics:
                name = 'hrest_' + thread_metric.lower()
                blor = jolo_tjson['value'][thread_metric]
                if thread_metric == 'requests':
                    self.local_vars.append({'name': name, 'timestamp': self.timestamp, 'value': blor, 'check_type': check_type, 'chart_type': 'Counter'})
                self.local_vars.append({'name': name, 'timestamp': self.timestamp, 'value': blor, 'check_type': check_type})
    
            for rated_metric in hrmetrics_rated:
                name = 'hrest_' + rated_metric.lower()
                blor = self.rate.record_value_rate('hrest_' + rated_metric + '_collection_time', jolo_tjson['value'][thread_metric], self.timestamp)
                self.local_vars.append({'name': name, 'timestamp': self.timestamp, 'value': blor, 'check_type': check_type})
    
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            try:
                lib.jolostart.do_joloikia(java, juser, jclass, hrest_url)
            except Exception as jolo:
                lib.pushdata.print_error(__name__, (jolo))
            pass
