import lib.record_rate
import lib.commonclient
import lib.puylogger
import lib.getconfig
import lib.basecheck
import json
import re

jetty_url = lib.getconfig.getparam('Jetty', 'stats')
# cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_type = 'jetty'
reaction = -3


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            data_dict = json.loads(lib.commonclient.httpget(__name__, jetty_url + '/java.lang:type=GarbageCollector,name=*'))

            for itme in data_dict['value'].items():
                nme = itme[1]['Name'].replace(' Generation', '').replace('ConcurrentMarkSweep', 'cms').lower().replace(' ', '_')
                if 'LastGcInfo' in itme[1] and itme[1]['LastGcInfo'] is not None:
                    vle = itme[1]['LastGcInfo']['duration']
                else:
                    vle = 0
                self.local_vars.append({'name': 'jetty_lastgcinfo', 'timestamp': self.timestamp, 'value': vle, 'check_type': check_type, 'extra_tag': {'gctype': nme}})
                for o in ('CollectionCount', 'CollectionTime'):
                    if o in itme[1]:
                        vle = itme[1][o]
                    else:
                        vle = 0
                    self.local_vars.append({'name': 'jetty_gc_' + o.lower(), 'timestamp': self.timestamp, 'value': vle, 'check_type': check_type, 'reaction': -1, 'extra_tag': {'gctype': nme}})

            heam_mem='java.lang:type=Memory'
            jolo_json = json.loads(lib.commonclient.httpget(__name__, jetty_url+'/'+heam_mem))
            jolo_keys = jolo_json['value']
            metr_name=('used', 'committed', 'max')
            heap_type=('NonHeapMemoryUsage', 'HeapMemoryUsage')
            for heap in heap_type:
                for metr in metr_name:
                    if heap == 'NonHeapMemoryUsage':
                        key='jetty_nonheap_'+ metr
                        mon_values=jolo_keys[heap][metr]
                        if metr == 'used':
                            self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': mon_values, 'check_type': check_type})
                        else:
                            self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': mon_values, 'check_type': check_type, 'reaction': reaction})
                    else:
                        key='jetty_heap_'+ metr
                        mon_values=jolo_keys[heap][metr]
                        if metr == 'used':
                            self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': mon_values, 'check_type': check_type})
                        else:
                            self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': mon_values, 'check_type': check_type, 'reaction': reaction})
            jolo_threads='java.lang:type=Threading'
            jolo_tjson = json.loads(lib.commonclient.httpget(__name__, jetty_url+'/'+jolo_threads))
            thread_metrics=('PeakThreadCount','ThreadCount','DaemonThreadCount')
            for thread_metric in thread_metrics:
                name='jetty_'+thread_metric.lower()
                vlor=jolo_tjson['value'][thread_metric]
                self.local_vars.append({'name': name, 'timestamp': self.timestamp, 'value': vlor, 'check_type': check_type})
    
            sessions = json.loads(lib.commonclient.httpget(__name__, jetty_url + '/org.eclipse.jetty.server.session:context=*,type=defaultsessioncache,id=*'))
            request = json.loads(lib.commonclient.httpget(__name__, jetty_url + '/org.eclipse.jetty.server.handler:type=statisticshandler,id=0'))
    
            counters = ['responses1xx', 'responses2xx', 'responses5xx', 'responses4xx']
            valuesss = ['requestsActive', 'dispatchedActive', 'asyncRequests', 'requestTimeMean']
    
            for v in sessions['value'].keys():
                if 'jetty' not in v:
                    self.local_vars.append({'name': 'jetty_active_sessions', 'timestamp': self.timestamp, 'value': sessions['value'][v]['sessionsCurrent'], 'reaction': reaction, 'check_type': check_type, 'extra_tag': {'webapp': re.split('org.eclipse.jetty.server.session:context=', v)[-1].split(',')[0]}})
    
            for v in counters:
                self.local_vars.append({'name': 'jetty_' + v, 'timestamp': self.timestamp, 'value': request['value'][v], 'check_type': check_type, 'chart_type': 'Counter'})
            for v in valuesss:
                self.local_vars.append({'name': 'jetty_' + v.lower(), 'timestamp': self.timestamp, 'value': request['value'][v], 'check_type': check_type})
    
            requests_rate = int(self.rate.record_value_rate('jetty_requests', request['value']['requests'], self.timestamp))
            self.local_vars.append({'name': 'jetty_requests_rate', 'timestamp': self.timestamp, 'value': requests_rate, 'check_type': check_type, 'chart_type': 'Rate'})
    
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
    
    
