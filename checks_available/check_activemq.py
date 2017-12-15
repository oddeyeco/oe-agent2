import lib.record_rate
import lib.commonclient
import lib.puylogger
import lib.getconfig
import lib.basecheck
import json

stats_url = lib.getconfig.getparam('ActiveMQ', 'stats')
activemq_auth = lib.getconfig.getparam('ActiveMQ', 'user')+':'+lib.getconfig.getparam('ActiveMQ', 'pass')
curl_auth = lib.getconfig.getparam('ActiveMQ', 'auth')
brokername = lib.getconfig.getparam('ActiveMQ', 'brokername')

check_type = 'activemq'
reaction = -3


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            # lib.puylogger.print_message(stats_url + '/java.lang:type=GarbageCollector,name=*')
            data_dict = json.loads(lib.commonclient.httpget(__name__, stats_url + '/java.lang:type=GarbageCollector,name=*', activemq_auth))
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
            jolo_json = json.loads(lib.commonclient.httpget(__name__, stats_url + '/' + heam_mem, activemq_auth))
            jolo_keys = jolo_json['value']
            metr_name = ('used', 'committed', 'max')
            heap_type = ('NonHeapMemoryUsage', 'HeapMemoryUsage')
            for heap in heap_type:
                for metr in metr_name:
                    if heap == 'NonHeapMemoryUsage':
                        key = 'activemq_nonheap_' + metr
                        mon_values = jolo_keys[heap][metr]
                        if metr == 'used':
                            self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': mon_values, 'check_type': check_type})
                        else:
                            self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': mon_values, 'check_type': check_type, 'reaction': reaction})
                    else:
                        key = 'activemq_heap_' + metr
                        mon_values = jolo_keys[heap][metr]
                        if metr == 'used':
                            self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': mon_values, 'check_type': check_type})
                        else:
                            self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': mon_values, 'check_type': check_type, 'reaction': reaction})
            if CMS is True:
                collector = ('java.lang:name=ParNew,type=GarbageCollector', 'java.lang:name=ConcurrentMarkSweep,type=GarbageCollector')
                for coltype in collector:
                    beans = json.loads(lib.commonclient.httpget(__name__, stats_url + '/' + coltype, activemq_auth))
                    LastGcInfo = beans['value']['LastGcInfo']['duration']
                    CollectionCount = beans['value']['CollectionCount']
                    CollectionTime = beans['value']['CollectionTime']
    
                    def push_metrics(preffix):
                        CollectionTime_rate = self.rate.record_value_rate('activemq_' + preffix + '_CollectionTime', CollectionTime, self.timestamp)
                        self.local_vars.append({'name': 'activemq_' + preffix + '_lastgcinfo', 'timestamp': self.timestamp, 'value': LastGcInfo, 'check_type': check_type})
                        self.local_vars.append({'name': 'activemq_' + preffix + '_collection_count', 'timestamp': self.timestamp, 'value': CollectionCount, 'check_type': check_type})
                        self.local_vars.append({'name': 'activemq_' + preffix + '_collectiontime', 'timestamp': self.timestamp, 'value': CollectionTime_rate, 'check_type': check_type, 'chart_type': 'Rate'})
    
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
                    j = json.loads(lib.commonclient.httpget(__name__, stats_url + v, activemq_auth))
                    name = 'LastGcInfo'
                    if k is 0:
                        try:
                            value = j['value'][name]['duration']
                            v = check_null(value)
                        except:
                            v = 0
                            pass
                        m_name = 'activemq_g1_old_lastgcinfo'
                    if k is 1:
                        value = j['value'][name]['duration']
                        v = check_null(value)
                        m_name = 'activemq_g1_young_lastgcinfo'
                    self.local_vars.append({'name': m_name, 'timestamp': self.timestamp, 'value': v, 'check_type': check_type})
    
                metr_keys = ('CollectionTime', 'CollectionCount')
                for k, v in enumerate(gc_g1):
                    j = json.loads(lib.commonclient.httpget(__name__, stats_url + v, activemq_auth))
                    if k is 0:
                        type = '_old_'
                    if k is 1:
                        type = '_young_'
                    for ky, vl in enumerate(metr_keys):
                        if ky is 0:
                            value = j['value'][vl]
                            v = check_null(value)
                            rate_key = vl + type
                            CollectionTime_rate = self.rate.record_value_rate('activemq_' + rate_key, v, self.timestamp)
                            self.local_vars.append({'name': 'activemq_g1' + type + vl.lower(), 'timestamp': self.timestamp, 'value': CollectionTime_rate, 'check_type': check_type, 'chart_type': 'Rate'})
                        if ky is 1:
                            value = j['value'][vl]
                            v = check_null(value)
                            self.local_vars.append({'name': 'activemq_g1' + type + vl.lower(), 'timestamp': self.timestamp, 'value': v, 'check_type': check_type, 'reaction': reaction})
            jolo_threads = 'java.lang:type=Threading'
            jolo_tjson = json.loads(lib.commonclient.httpget(__name__, stats_url + '/' + jolo_threads, activemq_auth))
            thread_metrics = ('PeakThreadCount', 'ThreadCount', 'DaemonThreadCount')
            for thread_metric in thread_metrics:
                name = 'activemq_' + thread_metric.lower()
                vlor = jolo_tjson['value'][thread_metric]
                self.local_vars.append({'name': name, 'timestamp': self.timestamp, 'value': vlor, 'check_type': check_type})
    
            brokerstats = json.loads(lib.commonclient.httpget(__name__, stats_url + '/org.apache.activemq:brokerName=' + brokername + ',type=Broker', activemq_auth))
            bstats = ['TotalConnectionsCount', 'TotalMessageCount', 'MemoryPercentUsage', 'TotalProducerCount',
                      'StorePercentUsage', 'TotalConsumerCount', 'TotalEnqueueCount', 'TotalDequeueCount']
            for s in bstats:
                self.local_vars.append({'name': 'activemq_' + s.lower(), 'timestamp': self.timestamp, 'value': brokerstats['value'][s], 'check_type': check_type})
    
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
    
    
