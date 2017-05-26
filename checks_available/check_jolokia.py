import lib.record_rate
import lib.pushdata
import lib.commonclient
import lib.puylogger
import lib.getconfig
import datetime
import json


jolokia_url = lib.getconfig.getparam('Jolokia', 'jolokia')
cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_type = 'Jolokia'
reaction = -3

def runcheck():
    try:
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
            
        jsondata=lib.pushdata.JonSon()
        jsondata.prepare_data()
        rate=lib.record_rate.ValueRate()
        timestamp = int(datetime.datetime.now().strftime("%s"))
        heam_mem='java.lang:type=Memory'
        jolo_json = json.loads(lib.commonclient.httpget(__name__, jolokia_url+'/'+heam_mem))
        jolo_keys = jolo_json['value']
        metr_name=('used', 'committed', 'max')
        heap_type=('NonHeapMemoryUsage', 'HeapMemoryUsage')
        for heap in heap_type:
            for metr in metr_name:
                if heap == 'NonHeapMemoryUsage':
                    key='jolokia_nonheap_'+ metr
                    mon_values=jolo_keys[heap][metr]
                    if metr == 'used':
                        jsondata.gen_data(key, timestamp, mon_values, lib.pushdata.hostname, check_type, cluster_name)
                    else:
                        jsondata.gen_data(key, timestamp, mon_values, lib.pushdata.hostname, check_type, cluster_name, reaction)
                else:
                    key='jolokia_heap_'+ metr
                    mon_values=jolo_keys[heap][metr]
                    if metr == 'used':
                        jsondata.gen_data(key, timestamp, mon_values, lib.pushdata.hostname, check_type, cluster_name)
                    else:
                        jsondata.gen_data(key, timestamp, mon_values, lib.pushdata.hostname, check_type, cluster_name, reaction)
        if CMS is True:
            collector = ('java.lang:name=ParNew,type=GarbageCollector', 'java.lang:name=ConcurrentMarkSweep,type=GarbageCollector')
            for coltype in collector:
                beans = json.loads(lib.commonclient.httpget(__name__, jolokia_url + '/' + coltype))
                LastGcInfo = beans['value']['LastGcInfo']['duration']
                CollectionCount = beans['value']['CollectionCount']
                CollectionTime = beans['value']['CollectionTime']
                def push_metrics(preffix):
                    jsondata.gen_data('jolokia_'+preffix+'_lastgcinfo', timestamp, LastGcInfo, lib.pushdata.hostname, check_type, cluster_name)
                    jsondata.gen_data('jolokia_'+preffix+'_collection_count', timestamp, CollectionCount, lib.pushdata.hostname, check_type, cluster_name)
                    CollectionTime_rate = rate.record_value_rate('jolokia_'+preffix+'_CollectionTime', CollectionTime, timestamp)
                    jsondata.gen_data('jolokia_'+preffix+'_CollectionTime', timestamp, CollectionTime_rate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')
                if coltype=='java.lang:name=ConcurrentMarkSweep,type=GarbageCollector':
                    push_metrics(preffix='CMS')
                if coltype == 'java.lang:name=ParNew,type=GarbageCollector':
                    push_metrics(preffix='ParNew')

        if G1 is True:
            gc_g1 = ('/java.lang:name=G1%20Old%20Generation,type=GarbageCollector','/java.lang:name=G1%20Young%20Generation,type=GarbageCollector')

            def check_null(value):
                if value is None:
                    value = 0
                    return value
                else:
                    return value

            for k, v in enumerate(gc_g1):
                # jj = urllib2.urlopen(jolokia_url + v, timeout=5)
                # j=json.load(jj)
                # jj.close()
                j = json.loads(lib.commonclient.httpget(__name__, jolokia_url + v))
                name='LastGcInfo'
                if k is 0:
                    try:
                        value = j['value'][name]['duration']
                        v = check_null(value)
                    except:
                        v=0
                        pass
                    m_name='jolokia_g1_old_lastgcinfo'
                if k is 1:
                    value = j['value'][name]['duration']
                    v = check_null(value)
                    m_name = 'jolokia_g1_young_lastgcinfo'
                jsondata.gen_data(m_name, timestamp, v, lib.pushdata.hostname, check_type, cluster_name)

            metr_keys = ('CollectionTime', 'CollectionCount')
            for k, v in enumerate(gc_g1):
                j = json.loads(lib.commonclient.httpget(__name__, jolokia_url + v))
                if k is 0 :
                    type='_old_'
                if k is 1:
                    type = '_young_'
                for ky, vl in enumerate(metr_keys):
                    if ky is 0:
                        value = j['value'][vl]
                        v = check_null(value)
                        rate_key=vl+type
                        CollectionTime_rate = rate.record_value_rate('jolokia_' + rate_key, v, timestamp)
                        jsondata.gen_data('jolokia_g1'+ type+ vl.lower(), timestamp, CollectionTime_rate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')
                    if ky is 1:
                        value = j['value'][vl]
                        v = check_null(value)
                        jsondata.gen_data('jolokia_g1' + type + vl.lower(), timestamp, v, lib.pushdata.hostname, check_type, cluster_name)
        jolo_threads='java.lang:type=Threading'
        jolo_tjson = json.loads(lib.commonclient.httpget(__name__, jolokia_url+'/'+jolo_threads))
        thread_metrics=('TotalStartedThreadCount','PeakThreadCount','ThreadCount','DaemonThreadCount')
        for thread_metric in thread_metrics:
            name='jolokia_'+thread_metric.lower()
            vlor=jolo_tjson['value'][thread_metric]
            jsondata.gen_data(name, timestamp, vlor, lib.pushdata.hostname, check_type, cluster_name)

        jsondata.put_json()

    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass


