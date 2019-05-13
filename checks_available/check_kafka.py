import lib.record_rate
import lib.getconfig
import lib.commonclient
import lib.puylogger
import lib.basecheck
import json

jolokia_url = lib.getconfig.getparam('Kafka', 'jolokia')
check_type = 'kafka'
data_dict = json.loads(lib.commonclient.httpget(__name__, jolokia_url + '/java.lang:type=GarbageCollector,name=*'))
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


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            jolo_mbeans = ('java.lang:type=Memory',
                         'kafka.server:type=BrokerTopicMetrics,name=*',
                         'kafka.network:name=*,request=FetchConsumer,type=RequestMetrics',
                         'kafka.network:name=*,request=Produce,type=RequestMetrics'
                         )

            data_dict = json.loads(lib.commonclient.httpget(__name__, jolokia_url + '/java.lang:type=GarbageCollector,name=*'))

            for itme in data_dict['value'].items():
                nme = itme[1]['Name'].replace(' Generation', '').lower().replace(' ', '_').replace('ConcurrentMarkSweep', 'cms')
                if 'LastGcInfo' in itme[1] and itme[1]['LastGcInfo'] is not None:
                    vle = itme[1]['LastGcInfo']['duration']
                else:
                    vle = 0
                self.local_vars.append({'name': 'kafka_lastgcinfo', 'timestamp': self.timestamp, 'value': vle, 'check_type': check_type, 'extra_tag': {'gctype': nme}})
                for o in ('CollectionCount', 'CollectionTime'):
                    if o in itme[1]:
                        vle = itme[1][o]
                    else:
                        vle = 0
                    self.local_vars.append({'name': 'kafka_gc_' + o.lower(), 'timestamp': self.timestamp, 'value': vle, 'check_type': check_type, 'reaction': -1, 'extra_tag': {'gctype': nme}})

            for beans in jolo_mbeans:
                jolo_json = json.loads(lib.commonclient.httpget(__name__, jolokia_url+'/'+beans))
                jolo_keys = jolo_json['value']
                # lib.puylogger.print_message(str(jolo_keys))
                if beans == 'java.lang:type=Memory':
                    metr_name=('used', 'committed')
                    heap_type=('NonHeapMemoryUsage', 'HeapMemoryUsage')
                    for heap in heap_type:
                        for metr in metr_name:
                            if heap == 'NonHeapMemoryUsage':
                                key='kafka_nonheap_'+ metr.lower()
                                mon_values=jolo_keys[heap][metr]
                                self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': mon_values, 'check_type': check_type})
                            else:
                                key='kafka_heap_'+ metr
                                mon_values=jolo_keys[heap][metr]
                                self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': mon_values, 'check_type': check_type})
                elif beans == 'kafka.server:type=BrokerTopicMetrics,name=*':
                    beans = ('TotalProduceRequestsPerSec', 'TotalFetchRequestsPerSec', 'BytesInPerSec', 'BytesOutPerSec',
                             'BytesRejectedPerSec', 'FailedFetchRequestsPerSec', 'FailedProduceRequestsPerSec', 'MessagesInPerSec')
                    for bean in beans:
                        m = 'kafka.server:name=' + bean + ',type=BrokerTopicMetrics'
                        value = jolo_json['value'][m]['OneMinuteRate']
                        self.local_vars.append({'name': 'kafka_' + bean.lower(), 'timestamp': self.timestamp, 'value': value, 'check_type': check_type})

            request_metrics = ('Produce', 'JoinGroup', 'FetchFollower', 'GroupCoordinator', 'OffsetCommit',
                               'LeaderAndIsr', 'Offsets', 'OffsetFetch', 'Fetch', 'FetchConsumer')
            lo = json.loads(lib.commonclient.httpget(__name__, jolokia_url + '/kafka.network:name=*,request=*,type=*'))
            for request_bean in request_metrics:
                    bname = 'kafka.network:name=RequestsPerSec,request=' + request_bean + ',type=RequestMetrics'
                    if bname in lo['value']:
                        counter = lo['value'][bname]['Count']
                        rated_value = self.rate.record_value_rate('kafka_' + bname, counter, self.timestamp)
                        self.local_vars.append({'name': 'kafka_' + request_bean.lower(), 'timestamp': self.timestamp, 'value': rated_value, 'check_type': check_type, 'chart_type': 'Rate'})
    
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
    
    
