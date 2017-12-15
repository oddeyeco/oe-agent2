import lib.record_rate
import lib.pushdata
import lib.puylogger
import lib.jolostart
import lib.getconfig
import lib.commonclient
import lib.basecheck
import json


jmx_url = lib.getconfig.getparam('JMX', 'jmx')

java = lib.getconfig.getparam('JMX', 'java')
juser = lib.getconfig.getparam('JMX', 'user')
jclass = lib.getconfig.getparam('JMX', 'class')
check_type = 'jmx'
reaction = -3

lib.jolostart.do_joloikia(java, juser, jclass, jmx_url)

class Check(lib.basecheck.CheckBase):

    def precheck(self):
    
        try:
            data_dict = json.loads(lib.commonclient.httpget(__name__, jmx_url + '/java.lang:type=GarbageCollector,name=*'))
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
            jolo_json = json.loads(lib.commonclient.httpget(__name__, jmx_url + '/' + heam_mem))
            jolo_keys = jolo_json['value']
            metr_name = ('used', 'committed', 'max')
            heap_type = ('NonHeapMemoryUsage', 'HeapMemoryUsage')
            for heap in heap_type:
                for metr in metr_name:
                    if heap == 'NonHeapMemoryUsage':
                        key = 'jmx_nonheap_' + metr
                        mon_values = jolo_keys[heap][metr]
                        if metr == 'used':
                            self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': mon_values, 'check_type': check_type})
                        else:
                            self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': mon_values, 'check_type': check_type, 'reaction': reaction})
                    else:
                        key = 'jmx_heap_' + metr
                        mon_values = jolo_keys[heap][metr]
                        if metr == 'used':
                            self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': mon_values, 'check_type': check_type})
                        else:
                            self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': mon_values, 'check_type': check_type, 'reaction': reaction})
            if CMS is True:
                collector = ('java.lang:name=ParNew,type=GarbageCollector', 'java.lang:name=ConcurrentMarkSweep,type=GarbageCollector')
                for coltype in collector:
                    beans = json.loads(lib.commonclient.httpget(__name__, jmx_url + '/' + coltype))
                    if beans['value']['LastGcInfo']:
                        LastGcInfo = beans['value']['LastGcInfo']['duration']
                    CollectionCount = beans['value']['CollectionCount']
                    CollectionTime = beans['value']['CollectionTime']
    
                    def push_metrics(preffix):
                        CollectionTime_rate = self.rate.record_value_rate('jmx_' + preffix + '_collection_time', CollectionTime, self.timestamp)
                        if 'LastGcInfo' in locals():
                            self.local_vars.append({'name': 'jmx_' + preffix + '_lastgcinfo', 'timestamp': self.timestamp, 'value': LastGcInfo, 'check_type': check_type})
    
                        self.local_vars.append({'name': 'jmx_' + preffix + '_collection_count', 'timestamp': self.timestamp, 'value': CollectionCount, 'check_type': check_type})
                        self.local_vars.append({'name': 'jmx_' + preffix + '_collection_time', 'timestamp': self.timestamp, 'value': CollectionTime_rate, 'check_type': check_type, 'chart_type': 'Rate'})
    
    
    
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
                    j = json.loads(lib.commonclient.httpget(__name__, jmx_url + v))
                    name = 'LastGcInfo'
                    if k is 0:
                        try:
                            value = j['value'][name]['duration']
                            v = check_null(value)
                        except:
                            v = 0
                            pass
                        m_name = 'jmx_G1_old_LastGcInfo'
                    if k is 1:
                        value = j['value'][name]['duration']
                        v = check_null(value)
                        m_name = 'jmx_G1_young_LastGcInfo'
                    self.local_vars.append({'name': m_name, 'timestamp': self.timestamp, 'value': v, 'check_type': check_type})
    
                metr_keys = ('CollectionTime', 'CollectionCount')
                for k, v in enumerate(gc_g1):
                    j = json.loads(lib.commonclient.httpget(__name__, jmx_url + v))
                    if k is 0:
                        type = '_old_'
                    if k is 1:
                        type = '_young_'
                    for ky, vl in enumerate(metr_keys):
                        if ky is 0:
                            value = j['value'][vl]
                            v = check_null(value)
                            rate_key = vl + type
                            CollectionTime_rate = self.rate.record_value_rate('jmx_' + rate_key, v, self.timestamp)
                            self.local_vars.append({'name': 'jmx_g1' + type + vl, 'timestamp': self.timestamp, 'value': CollectionTime_rate, 'check_type': check_type, 'chart_type': 'Rate'})
                        if ky is 1:
                            value = j['value'][vl]
                            v = check_null(value)
                            self.local_vars.append({'name': 'jmx_g1' + type + vl, 'timestamp': self.timestamp, 'value': v, 'check_type': check_type})
            jolo_threads = 'java.lang:type=Threading'
            jolo_tjson = json.loads(lib.commonclient.httpget(__name__, jmx_url + '/' + jolo_threads))
            thread_metrics = ('TotalStartedThreadCount', 'PeakThreadCount', 'ThreadCount', 'DaemonThreadCount')
            for thread_metric in thread_metrics:
                name = 'jmx_' + thread_metric.lower()
                vlor = jolo_tjson['value'][thread_metric]
                self.local_vars.append({'name': name, 'timestamp': self.timestamp, 'value': vlor, 'check_type': check_type})
    
    
        except Exception as e:
            lib.pushdata.print_error(__name__, (e))
            try:
                lib.jolostart.do_joloikia(java, juser, jclass, jmx_url)
            except Exception as jolo:
                lib.puylogger.print_message(__name__ + ' Error : ' + str(jolo))
            pass
    
    
