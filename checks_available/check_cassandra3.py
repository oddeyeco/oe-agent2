import lib.getconfig
import lib.basecheck
import lib.commonclient
import lib.record_rate
import lib.puylogger
import json

jolokia_url = lib.getconfig.getparam('Cassandra', 'jolokia')
check_type = 'cassandra'


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            cassa_cql_metrics = json.loads(lib.commonclient.httpget(__name__, jolokia_url+'/org.apache.cassandra.metrics:type=CQL,name=*'))
            cassa_cache_metrics = json.loads(lib.commonclient.httpget(__name__, jolokia_url+'/org.apache.cassandra.metrics:type=Cache,scope=*,name=*'))
            cassa_copmaction = json.loads(lib.commonclient.httpget(__name__, jolokia_url+'/org.apache.cassandra.metrics:type=Compaction,name=*'))
            cassa_latency = json.loads(lib.commonclient.httpget(__name__, jolokia_url + '/org.apache.cassandra.metrics:type=ClientRequest,scope=*,name=Latency'))
            cql_statemets = ('PreparedStatementsExecuted', 'RegularStatementsExecuted')
            for cql_statement in cql_statemets:
                mon_value = cassa_cql_metrics['value']['org.apache.cassandra.metrics:name=' + cql_statement + ',type=CQL']['Count']
                mon_name = 'cassa_cql_'+cql_statement
                if mon_value is not None:
                    if mon_value is 0:
                        self.local_vars.append({'name': mon_name.lower(), 'timestamp': self.timestamp, 'value': mon_value, 'check_type': check_type})
                    else:
                        value_rate = self.rate.record_value_rate('cql_'+mon_name, mon_value, self.timestamp)
                        self.local_vars.append({'name': mon_name.lower(), 'timestamp': self.timestamp, 'value': value_rate, 'check_type': check_type, 'chart_type': 'Rate'})
            latency_metrics = ('Read', 'ViewWrite', 'RangeSlice', 'CASRead', 'CASWrite', 'Write')

            for latency_metric in latency_metrics:
                mon_value = cassa_latency['value']['org.apache.cassandra.metrics:name=Latency,scope=' + latency_metric + ',type=ClientRequest']['OneMinuteRate']
                mon_name = 'cassa_latency_' + str(latency_metric).lower()
                self.local_vars.append({'name': mon_name, 'timestamp': self.timestamp, 'value': mon_value, 'check_type': check_type})

            cache_metrics = ('Hits,scope=KeyCache', 'Hits,scope=RowCache', 'Requests,scope=KeyCache', 'Requests,scope=RowCache')
            for cache_metric in cache_metrics:
                mon_value = cassa_cache_metrics['value']['org.apache.cassandra.metrics:name=' + cache_metric + ',type=Cache']['OneMinuteRate']
                mon_name = 'cassa_' + str(cache_metric).replace(',scope=', '_')
                self.local_vars.append({'name': mon_name.lower(), 'timestamp': self.timestamp, 'value': mon_value, 'check_type': check_type})
    
            copaction_tasks = cassa_copmaction['value']['org.apache.cassandra.metrics:name=PendingTasks,type=Compaction']['Value']
            self.local_vars.append({'name': 'cassa_compaction_pending', 'timestamp': self.timestamp, 'value': copaction_tasks, 'check_type': check_type})

            heam_mem = 'java.lang:type=Memory'
            jolo_json = json.loads(lib.commonclient.httpget(__name__, jolokia_url + '/' + heam_mem))
            jolo_keys = jolo_json['value']
            metr_name = ('used', 'committed', 'max')
            heap_type = ('NonHeapMemoryUsage', 'HeapMemoryUsage')
            for heap in heap_type:
                for metr in metr_name:
                    if heap == 'NonHeapMemoryUsage':
                        key = 'cassa_nonheap_' + metr
                        mon_values = jolo_keys[heap][metr]
                        if metr == 'used':
                            self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': mon_values, 'check_type': check_type})
                        else:
                            self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': mon_values, 'check_type': check_type, 'reaction': -3})
                    else:
                        key = 'cassa_heap_' + metr
                        mon_values = jolo_keys[heap][metr]
                        if metr == 'used':
                            self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': mon_values, 'check_type': check_type})
                        else:
                            self.local_vars.append({'name': key, 'timestamp': self.timestamp, 'value': mon_values, 'check_type': check_type, 'reaction': -3})

            data_dict = json.loads(lib.commonclient.httpget(__name__, jolokia_url + '/java.lang:type=GarbageCollector,name=*'))

            for itme in data_dict['value'].items():
                nme = itme[1]['Name']
                if nme == 'ConcurrentMarkSweep':
                    nme = 'cms'
                else:
                    nme = nme.lower()
                if 'LastGcInfo' in itme[1]:
                    vle = itme[1]['LastGcInfo']['duration']
                else:
                    vle = 0
                self.local_vars.append({'name': 'cassa_lastgcinfo', 'timestamp': self.timestamp, 'value': vle, 'check_type': check_type, 'extra_tag': {'gctype': nme}})
                for o in ('CollectionCount', 'CollectionTime'):
                    if o in itme[1]:
                        vle = itme[1][o]
                    else:
                        vle = 0
                    self.local_vars.append({'name': 'cassa_gc_' + o.lower(), 'timestamp': self.timestamp, 'value': vle, 'check_type': check_type, 'reaction': -1, 'extra_tag': {'gctype': nme}})

            jolo_threads = 'java.lang:type=Threading'
            jolo_tjson = json.loads(lib.commonclient.httpget(__name__, jolokia_url + '/' + jolo_threads))

            for thread_metric in ('TotalStartedThreadCount', 'PeakThreadCount', 'ThreadCount', 'DaemonThreadCount'):
                name = 'cassa_' + thread_metric.lower()
                vlor = jolo_tjson['value'][thread_metric]
                self.local_vars.append({'name': name, 'timestamp': self.timestamp, 'value': vlor, 'check_type': check_type})
    
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
