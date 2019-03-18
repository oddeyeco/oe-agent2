import lib.record_rate
import lib.commonclient
import lib.puylogger
import lib.getconfig
import lib.basecheck
import json


jolokia_url = lib.getconfig.getparam('Jolokia', 'jolokia')
check_type = 'jolokia'
reaction = -3


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            data_dict = json.loads(lib.commonclient.httpget(__name__, jolokia_url + '/java.lang:type=GarbageCollector,name=*'))
            for itme in data_dict['value'].items():
                nme = itme[1]['Name'].replace(' Generation', '').replace('ConcurrentMarkSweep', 'cms').lower().replace(' ', '_')
                if 'LastGcInfo' in itme[1] and itme[1]['LastGcInfo'] is not None:
                    vle = itme[1]['LastGcInfo']['duration']
                else:
                    vle = 0
                self.local_vars.append({'name': 'jolokia_lastgcinfo', 'timestamp': self.timestamp, 'value': vle, 'check_type': check_type, 'extra_tag': {'gctype': nme}})
                for o in ('CollectionCount', 'CollectionTime'):
                    if o in itme[1]:
                        vle = itme[1][o]
                    else:
                        vle = 0
                    self.local_vars.append({'name': 'jolokia_gc_' + o.lower(), 'timestamp': self.timestamp, 'value': vle, 'check_type': check_type, 'reaction': -1, 'extra_tag': {'gctype': nme}})

            heam_mem = 'java.lang:type=Memory'
            jolo_json = json.loads(lib.commonclient.httpget(__name__, jolokia_url+'/'+heam_mem))
            metr_name = ('used', 'committed', 'max')
            heap_type = ('NonHeapMemoryUsage', 'HeapMemoryUsage')
            for heap in heap_type:
                for metr in metr_name:
                    if heap == 'NonHeapMemoryUsage':
                        key = 'jolokia_nonheap_' + metr
                        mon_values = jolo_json['value'][heap][metr]
                        if metr == 'used':
                            self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': mon_values, 'check_type': check_type})
                        else:
                            self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': mon_values, 'check_type': check_type, 'reaction': reaction})
                    else:
                        key = 'jolokia_heap_' + metr
                        mon_values = jolo_json['value'][heap][metr]
                        if metr == 'used':
                            self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': mon_values, 'check_type': check_type})
                        else:
                            self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': mon_values, 'check_type': check_type, 'reaction': reaction})
            jolo_threads = 'java.lang:type=Threading'
            jolo_tjson = json.loads(lib.commonclient.httpget(__name__, jolokia_url+'/'+jolo_threads))
            thread_metrics = ('PeakThreadCount', 'ThreadCount', 'DaemonThreadCount')
            for thread_metric in thread_metrics:
                name = 'jolokia_' + thread_metric.lower()
                vlor = jolo_tjson['value'][thread_metric]
                self.local_vars.append({'name': name, 'timestamp': self.timestamp, 'value': vlor, 'check_type': check_type})
    
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
