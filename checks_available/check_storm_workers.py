import lib.puylogger
import lib.pushdata
import lib.commonclient
import lib.getconfig
import lib.basecheck
import json


worker_host = lib.getconfig.getparam('Storm', 'host')
worker_port = lib.getconfig.getparam('Storm', 'port').split(',')
worker_path = lib.getconfig.getparam('Storm', 'path')
cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_type = 'Storm'


class Check(lib.basecheck.CheckBase):

    def precheck(self):
    
        try:
    
            for port in worker_port:
                try:
                    storm_url = 'http://' + worker_host + ':' + port + worker_path
                    data_dict = json.loads(lib.commonclient.httpget(__name__, storm_url + '/java.lang:type=GarbageCollector,name=*'))
                    ConcurrentMarkSweep = 'java.lang:name=ConcurrentMarkSweep,type=GarbageCollector'
                    G1Gc = 'java.lang:name=G1 Young Generation,type=GarbageCollector'
    
                    if ConcurrentMarkSweep in data_dict['value']:
                        CMS = True
                        G1 = False
    
                    if G1Gc in data_dict['value']:
                        CMS = False
                        G1 = True
    
                    heam_mem = 'java.lang:type=Memory'
                    jolo_json = json.loads(lib.commonclient.httpget(__name__, storm_url+'/'+heam_mem))
                    jolo_keys = jolo_json['value']
                    metr_name = ('used', 'committed', 'max')
                    heap_type = ('NonHeapMemoryUsage', 'HeapMemoryUsage')
                    for heap in heap_type:
                        for metr in metr_name:
                            if heap == 'NonHeapMemoryUsage':
                                key = 'storm_nonheap_'+ metr
                                mon_values = jolo_keys[heap][metr]
                                self.local_vars.append({'name':key, 'timestamp': self.timestamp, 'value':mon_values, 'check_type': check_type, 'extra_tag':{'workerport': port}})
    
                            else:
                                key = 'storm_heap_'+ metr
                                mon_values = jolo_keys[heap][metr]
                                self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': mon_values, 'check_type': check_type, 'extra_tag':{'workerport': port}})
                    if CMS is True:
                        collector = ('java.lang:name=ParNew,type=GarbageCollector', 'java.lang:name=ConcurrentMarkSweep,type=GarbageCollector')
                        for coltype in collector:
                            beans = json.loads(lib.commonclient.httpget(__name__, storm_url + '/' + coltype))
    
                            lastgcinfo = beans['value']['LastGcInfo']['duration']
                            collectioncount = beans['value']['CollectionCount']
                            collectiontime = beans['value']['CollectionTime']
                            def push_metrics(preffix):
                                collectiontime_rate = self.rate.record_value_rate('storm_' + port + '_' + ''+preffix+'_collection_time', collectiontime, self.timestamp)
    
                                self.local_vars.append({'name': 'storm_' + preffix + '_lastgcinfo', 'timestamp': self.timestamp, 'value': lastgcinfo, 'check_type': check_type, 'extra_tag':{'workerport': port}})
                                self.local_vars.append({'name': 'storm_' + preffix + '_collection_count', 'timestamp': self.timestamp, 'value': collectioncount, 'check_type': check_type, 'extra_tag':{'workerport': port}})
                                self.local_vars.append({'name': 'storm_' + preffix + '_collection_time', 'timestamp': self.timestamp, 'value': collectiontime_rate, 'check_type': check_type, 'extra_tag':{'workerport': port}})
    
    
                            if coltype == 'java.lang:name=ConcurrentMarkSweep,type=GarbageCollector':
                                push_metrics(preffix='cms')
                            if coltype == 'java.lang:name=ParNew,type=GarbageCollector':
                                push_metrics(preffix='parnew')
    
                    if G1 is True:
                        gc_g1 = ('/java.lang:name=G1%20Old%20Generation,type=GarbageCollector','/java.lang:name=G1%20Young%20Generation,type=GarbageCollector')
    
                        def check_null(value):
                            if value is None:
                                value = 0
                                return value
                            else:
                                return value
    
    
    
                        for k, v in enumerate(gc_g1):
                            j = json.loads(lib.commonclient.httpget(__name__, storm_url + v))
                            name='LastGcInfo'
                            if k is 0:
                                value = j['value'][name]
                                v = check_null(value)
                                m_name = 'storm_' + port + '_' + 'g1_old_lastgcinfo'
                            if k is 1:
                                value = j['value'][name]['duration']
                                v = check_null(value)
                            self.local_vars.append({'name': 'storm_g1_young_lastgcinfo', 'timestamp': self.timestamp, 'value': v, 'check_type': check_type, 'extra_tag':{'workerport': port}})

                        metr_keys = ('CollectionTime', 'CollectionCount')
                        for k, v in enumerate(gc_g1):
                            j = json.loads(lib.commonclient.httpget(__name__, storm_url + v))
                            if k is 0 :
                                type='_old_'
                            if k is 1:
                                type = '_young_'
                            for ky, vl in enumerate(metr_keys):
                                if ky is 0:
                                    value = j['value'][vl]
                                    v = check_null(value)
                                    rate_key = vl+type
                                    collectiontime_rate = self.rate.record_value_rate('storm_' + port + '_' + '' + rate_key, v, self.timestamp)
                                    self.local_vars.append({'name': 'storm_g1' + type + vl.lower(), 'timestamp': self.timestamp, 'value': collectiontime_rate, 'chart_type': 'Rate', 'check_type': check_type, 'extra_tag':{'workerport': port}})
                                if ky is 1:
                                    value = j['value'][vl]
                                    v = check_null(value)
                                    self.local_vars.append({'name': 'storm_g1' + type + vl.lower(), 'timestamp': self.timestamp, 'value': v, 'check_type': check_type, 'reaction': -3, 'extra_tag':{'workerport': port}})
                except Exception as e:
                    lib.puylogger.print_message(__name__ + ' Error : ' + str(e) + ' ' + str(port))
                    pass
    
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
    
    
# self.local_vars.append({'name':  rxname, 'timestamp': self.timestamp, 'value':rxrate, 'chart_type': 'Rate', 'check_type': check_type, 'reaction': 0, 'extra_tag':{'device': nic}})
# self.local_vars.append({'name': 'storm_' + port + '_' + 'g1' + type + vl.lower(), 'timestamp': self.timestamp, 'value': collectiontime_rate, 'chart_type': 'Rate', 'check_type': check_type})