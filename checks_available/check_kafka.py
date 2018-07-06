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
                         'kafka.network:name=RequestsPerSec,request=FetchConsumer,type=RequestMetrics',
                         'kafka.network:name=RequestsPerSec,request=Produce,type=RequestMetrics'
                         )
            if G1 is True:
                gc_young_json = json.loads(lib.commonclient.httpget(__name__, jolokia_url + '/java.lang:name=G1%20Young%20Generation,type=GarbageCollector'))
                gc_old_json = json.loads(lib.commonclient.httpget(__name__, jolokia_url + '/java.lang:name=G1%20Old%20Generation,type=GarbageCollector'))
                for name in ('LastGcInfo','CollectionTime','CollectionCount'):
                    value = gc_old_json['value'][name]
                    if value is None:
                        value = 0
                    if name == 'CollectionTime':
                        values_rate = self.rate.record_value_rate(name, value, self.timestamp)
                        key = 'kafka_gc_old_' + name.lower()
                        self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': values_rate, 'check_type': check_type, 'chart_type': 'Rate'})
                    else:
                        key = 'kafka_gc_old_' + name.lower()
                        self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': value, 'check_type': check_type})
                for name in ('LastGcInfo', 'CollectionTime', 'CollectionCount'):
                    if name == 'LastGcInfo':
                        vl = gc_young_json['value'][name]['duration']
                        if vl is None:
                            vl = 0
                        key = 'kafka_gc_young_' + name.lower()
                        self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': vl, 'check_type': check_type})
                    if name == 'CollectionTime':
                        vl = gc_young_json['value'][name]
                        if vl is None:
                            vl = 0
                        key = 'kafka_gc_young_' + name.lower()
                        vl_rate = self.rate.record_value_rate(key, vl, self.timestamp)
                        self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': vl_rate, 'check_type': check_type, 'chart_type': 'Rate'})
                    if name == 'CollectionCount':
                        vl = gc_young_json['value'][name]
                        if vl is None:
                            vl = 0
                        key = 'kafka_gc_young_' + name.lower()
                        self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': vl, 'check_type': check_type, 'reaction': -3})

            for beans in jolo_mbeans:
                jolo_json = json.loads(lib.commonclient.httpget(__name__, jolokia_url+'/'+beans))
                jolo_keys = jolo_json['value']
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
                elif beans == 'kafka.server:type=Fetch':
                    value= jolo_keys['queue-size']
                    name = 'kafka_queuesize_'+beans.split('=')[1].lower()
                    values_rate = self.rate.record_value_rate(name, value, self.timestamp)
                    if values_rate >= 0:
                        self.local_vars.append({'name': name, 'timestamp': self.timestamp, 'value': values_rate, 'check_type': check_type, 'chart_type': 'Rate'})

                elif beans == 'kafka.server:type=Produce':
                    value= jolo_keys['queue-size']
                    name = 'kafka_queuesize_'+beans.split('=')[1].lower()
                    values_rate = self.rate.record_value_rate(name, value, self.timestamp)
                    if values_rate >= 0:
                        self.local_vars.append({'name': name, 'timestamp': self.timestamp, 'value': values_rate, 'check_type': check_type, 'chart_type': 'Rate'})
                elif beans == 'kafka.server:type=BrokerTopicMetrics,name=*':
                    beans = ('TotalProduceRequestsPerSec', 'BytesInPerSec', 'BytesOutPerSec', 'BytesRejectedPerSec', 'FailedFetchRequestsPerSec', 'FailedProduceRequestsPerSec', 'MessagesInPerSec')
                    for bean in beans:
                        m = 'kafka.server:name=' + bean + ',type=BrokerTopicMetrics'
                        value = jolo_json['value'][m]['OneMinuteRate']
                        self.local_vars.append({'name': 'kafka_' + bean.lower(), 'timestamp': self.timestamp, 'value': value, 'check_type': check_type})

            request_metrics = ('Produce', 'JoinGroup', 'FetchFollower', 'GroupCoordinator', 'OffsetCommit',
                               'LeaderAndIsr', 'Offsets', 'OffsetFetch', 'Fetch', 'FetchConsumer')
            lo = json.loads(lib.commonclient.httpget(__name__, jolokia_url + '/kafka.network:name=RequestsPerSec,request=*,type=*'))
            for request_bean in request_metrics:
                    bname = 'kafka.network:name=RequestsPerSec,request=' + request_bean + ',type=RequestMetrics'
                    # lib.puylogger.print_message(bname)
                    if bname in lo['value']:
                        counter = lo['value'][bname]['Count']
                        rated_value = self.rate.record_value_rate('kafka_' + bname, counter, self.timestamp)
                        self.local_vars.append({'name': 'kafka_' + request_bean.lower(), 'timestamp': self.timestamp, 'value': rated_value, 'check_type': check_type, 'chart_type': 'Rate'})
    
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
    
    
