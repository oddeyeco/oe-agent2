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

                    for itme in data_dict['value'].items():
                        nme = itme[1]['Name'].replace(' Generation', '').replace('ConcurrentMarkSweep', 'cms').lower().replace(' ', '_')
                        if 'LastGcInfo' in itme[1] and itme[1]['LastGcInfo'] is not None:
                            vle = itme[1]['LastGcInfo']['duration']
                        else:
                            vle = 0
                        self.local_vars.append({'name': 'storm_lastgcinfo', 'timestamp': self.timestamp, 'value': vle, 'check_type': check_type, 'extra_tag': {'gctype': nme, 'workerport': port}})
                        for o in ('CollectionCount', 'CollectionTime'):
                            if o in itme[1]:
                                vle = itme[1][o]
                            else:
                                vle = 0
                            self.local_vars.append({'name': 'storm_gc_' + o.lower(), 'timestamp': self.timestamp, 'value': vle, 'check_type': check_type, 'reaction': -1, 'extra_tag': {'gctype': nme, 'workerport': port}})

                    heam_mem = 'java.lang:type=Memory'
                    jolo_json = json.loads(lib.commonclient.httpget(__name__, storm_url+'/' + heam_mem))
                    jolo_keys = jolo_json['value']
                    metr_name = ('used', 'committed', 'max')
                    heap_type = ('NonHeapMemoryUsage', 'HeapMemoryUsage')
                    for heap in heap_type:
                        for metr in metr_name:
                            if heap == 'NonHeapMemoryUsage':
                                key = 'storm_nonheap_' + metr
                                mon_values = jolo_keys[heap][metr]
                                self.local_vars.append({'name':key, 'timestamp': self.timestamp, 'value':mon_values, 'check_type': check_type, 'extra_tag':{'workerport': port}})

                            else:
                                key = 'storm_heap_'+ metr
                                mon_values = jolo_keys[heap][metr]
                                self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': mon_values, 'check_type': check_type, 'extra_tag':{'workerport': port}})
                except Exception as e:
                    lib.puylogger.print_message(__name__ + ' Error : ' + str(e) + ' ' + str(port))
                    pass
    
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
