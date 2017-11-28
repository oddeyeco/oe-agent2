import lib.record_rate
import lib.commonclient
import lib.puylogger
import lib.getconfig
import datetime
import json
import re

jetty_url = lib.getconfig.getparam('Jetty', 'stats')
cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_type = 'jetty'
reaction = -3


def runcheck():
    local_vars = []
    try:
        data_dict = json.loads(lib.commonclient.httpget(__name__, jetty_url + '/java.lang:type=GarbageCollector,name=*'))
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
            
        rate=lib.record_rate.ValueRate()
        timestamp = int(datetime.datetime.now().strftime("%s"))
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
                        local_vars.append({'name': key, 'timestamp': timestamp, 'value': mon_values, 'check_type': check_type})
                    else:
                        local_vars.append({'name': key, 'timestamp': timestamp, 'value': mon_values, 'check_type': check_type, 'reaction': reaction})
                else:
                    key='jetty_heap_'+ metr
                    mon_values=jolo_keys[heap][metr]
                    if metr == 'used':
                        local_vars.append({'name': key, 'timestamp': timestamp, 'value': mon_values, 'check_type': check_type})
                    else:
                        local_vars.append({'name': key, 'timestamp': timestamp, 'value': mon_values, 'check_type': check_type, 'reaction': reaction})
        if CMS is True:
            collector = ('java.lang:name=ParNew,type=GarbageCollector', 'java.lang:name=ConcurrentMarkSweep,type=GarbageCollector')
            for coltype in collector:
                beans = json.loads(lib.commonclient.httpget(__name__, jetty_url + '/' + coltype))
                LastGcInfo = beans['value']['LastGcInfo']['duration']
                CollectionCount = beans['value']['CollectionCount']
                CollectionTime = beans['value']['CollectionTime']
                def push_metrics(preffix):
                    CollectionTime_rate = rate.record_value_rate('jetty_'+preffix+'_CollectionTime', CollectionTime, timestamp)
                    local_vars.append({'name': 'jetty_'+preffix+'_lastgcinfo', 'timestamp': timestamp, 'value': LastGcInfo, 'check_type': check_type})
                    local_vars.append({'name': 'jetty_' + preffix + '_collection_count', 'timestamp': timestamp, 'value': CollectionCount, 'check_type': check_type})
                    local_vars.append({'name': 'jetty_' + preffix + '_CollectionTime', 'timestamp': timestamp, 'value': CollectionTime_rate, 'check_type': check_type, 'chart_type': 'Rate'})

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
                j = json.loads(lib.commonclient.httpget(__name__, jetty_url + v))
                name='LastGcInfo'
                if k is 0:
                    try:
                        value = j['value'][name]['duration']
                        v = check_null(value)
                    except:
                        v=0
                        pass
                    m_name='jetty_g1_old_lastgcinfo'
                if k is 1:
                    value = j['value'][name]['duration']
                    v = check_null(value)
                    m_name = 'jetty_g1_young_lastgcinfo'
                local_vars.append({'name': m_name, 'timestamp': timestamp, 'value': v, 'check_type': check_type})

            metr_keys = ('CollectionTime', 'CollectionCount')
            for k, v in enumerate(gc_g1):
                j = json.loads(lib.commonclient.httpget(__name__, jetty_url + v))
                if k is 0 :
                    type='_old_'
                if k is 1:
                    type = '_young_'
                for ky, vl in enumerate(metr_keys):
                    if ky is 0:
                        value = j['value'][vl]
                        v = check_null(value)
                        rate_key=vl+type
                        CollectionTime_rate = rate.record_value_rate('jetty_' + rate_key, v, timestamp)
                        local_vars.append({'name': 'jetty_g1' + type + vl.lower(), 'timestamp': timestamp, 'value': CollectionTime_rate, 'check_type': check_type, 'chart_type': 'Rate'})
                    if ky is 1:
                        value = j['value'][vl]
                        v = check_null(value)
                        local_vars.append({'name': 'jetty_g1' + type + vl.lower(), 'timestamp': timestamp, 'value': v, 'check_type': check_type, 'reaction': reaction})
        jolo_threads='java.lang:type=Threading'
        jolo_tjson = json.loads(lib.commonclient.httpget(__name__, jetty_url+'/'+jolo_threads))
        thread_metrics=('PeakThreadCount','ThreadCount','DaemonThreadCount')
        for thread_metric in thread_metrics:
            name='jetty_'+thread_metric.lower()
            vlor=jolo_tjson['value'][thread_metric]
            local_vars.append({'name': name, 'timestamp': timestamp, 'value': vlor, 'check_type': check_type})

        sessions = json.loads(lib.commonclient.httpget(__name__, jetty_url + '/org.eclipse.jetty.server.session:context=*,type=defaultsessioncache,id=*'))
        request = json.loads(lib.commonclient.httpget(__name__, jetty_url + '/org.eclipse.jetty.server.handler:type=statisticshandler,id=0'))

        counters = ['responses1xx', 'responses2xx', 'responses5xx', 'responses4xx']
        valuesss = ['requestsActive', 'dispatchedActive', 'asyncRequests', 'requestTimeMean']

        for v in sessions['value'].keys():
            if 'jolokia' not in v:
                local_vars.append({'name': 'jetty_active_sessions', 'timestamp': timestamp, 'value': sessions['value'][v]['sessionsCurrent'], 'reaction': reaction, 'check_type': check_type, 'extra_tag': {'webapp': re.split('org.eclipse.jetty.server.session:context=', v)[-1].split(',')[0]}})

        for v in counters:
            local_vars.append({'name': 'jetty_' + v, 'timestamp': timestamp, 'value': request['value'][v], 'check_type': check_type, 'chart_type': 'Counter'})
        for v in valuesss:
            local_vars.append({'name': 'jetty_' + v.lower(), 'timestamp': timestamp, 'value': request['value'][v], 'check_type': check_type})

        requests_rate = int(rate.record_value_rate('jetty_requests', request['value']['requests'], timestamp))
        local_vars.append({'name': 'jetty_requests_rate', 'timestamp': timestamp, 'value': requests_rate, 'check_type': check_type, 'chart_type': 'Rate'})

        return local_vars
    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass


