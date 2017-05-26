import lib.getconfig
import datetime
import json
import lib.commonclient
import lib.pushdata
import lib.record_rate
import lib.puylogger




jolokia_url = lib.getconfig.getparam('Cassandra', 'jolokia')
cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_type = 'cassandra'
reaction=-3

def runcheck():
    try:
        jsondata = lib.pushdata.JonSon()
        jsondata.prepare_data()
        rate = lib.record_rate.ValueRate()
        timestamp = int(datetime.datetime.now().strftime("%s"))


        java_lang_metrics = json.loads(lib.commonclient.httpget(__name__, jolokia_url+'/java.lang:type=Memory'))
        cassa_cql_metrics = json.loads(lib.commonclient.httpget(__name__, jolokia_url+'/org.apache.cassandra.metrics:type=CQL,name=*'))
        cassa_cache_metrics = json.loads(lib.commonclient.httpget(__name__, jolokia_url+'/org.apache.cassandra.metrics:type=Cache,scope=*,name=*'))
        cassa_copmaction = json.loads(lib.commonclient.httpget(__name__, jolokia_url+'/org.apache.cassandra.metrics:type=Compaction,name=*'))

        jmetr_name = ('used', 'committed')
        jheap_type = ('NonHeapMemoryUsage', 'HeapMemoryUsage')
        for heap in jheap_type:
            for metr in jmetr_name:
                if heap == 'NonHeapMemoryUsage':
                    key = 'cassa_nonheap_' + metr
                    mon_values = java_lang_metrics['value'][heap][metr]
                    jsondata.gen_data(key, timestamp, mon_values, lib.pushdata.hostname, check_type, cluster_name, reaction)
                else:
                    key = 'cassa_heap_' + metr
                    mon_values = java_lang_metrics['value'][heap][metr]
                    jsondata.gen_data(key, timestamp, mon_values, lib.pushdata.hostname, check_type, cluster_name, reaction)

        cql_statemets = ('PreparedStatementsExecuted', 'RegularStatementsExecuted')
        for cql_statement in cql_statemets:
            mon_value = cassa_cql_metrics['value']['org.apache.cassandra.metrics:name=' + cql_statement + ',type=CQL']['Count']
            mon_name = 'cassa_cql_'+cql_statement
            if mon_value is not None:
                if mon_value is 0:
                    jsondata.gen_data(mon_name, timestamp, mon_value, lib.pushdata.hostname, check_type, cluster_name)
                else:
                    value_rate=rate.record_value_rate('cql_'+mon_name, mon_value, timestamp)
                    jsondata.gen_data(mon_name.lower(), timestamp, value_rate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')

        cache_metrics = ('Hits,scope=KeyCache', 'Requests,scope=KeyCache', 'Requests,scope=RowCache', 'Hits,scope=RowCache')
        for cache_metric in cache_metrics:
            mon_value = cassa_cache_metrics['value']['org.apache.cassandra.metrics:name=' + cache_metric + ',type=Cache']['OneMinuteRate']
            mon_name = 'cassa_'+ str(cache_metric).replace(',scope=', '_')
            jsondata.gen_data(mon_name.lower(), timestamp, mon_value, lib.pushdata.hostname, check_type, cluster_name)

        copaction_tasks = cassa_copmaction['value']['org.apache.cassandra.metrics:name=PendingTasks,type=Compaction']['Value']
        jsondata.gen_data('cassa_compaction_pending', timestamp, copaction_tasks, lib.pushdata.hostname, check_type, cluster_name)

        jsondata.put_json()

    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass