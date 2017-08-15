import lib.puylogger
import lib.record_rate
import lib.pushdata
import lib.commonclient
import lib.getconfig
import datetime
import json


worker_host = lib.getconfig.getparam('Storm', 'host')
worker_port = lib.getconfig.getparam('Storm', 'port').split(',')
worker_path = lib.getconfig.getparam('Storm', 'path')
cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_type = 'Storm'


def runcheck():
    try:
        local_vars = []
        rate = lib.record_rate.ValueRate()
        timestamp = int(datetime.datetime.now().strftime("%s"))

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
                            key = 'storm_' + port + '_' + 'nonheap_'+ metr
                            mon_values = jolo_keys[heap][metr]
                            local_vars.append({'name':key, 'timestamp': timestamp, 'value':mon_values, 'check_type': check_type})

                        else:
                            key = 'storm_' + port + '_' + 'heap_'+ metr
                            mon_values = jolo_keys[heap][metr]
                            local_vars.append({'name': key, 'timestamp': timestamp, 'value': mon_values, 'check_type': check_type})
                if CMS is True:
                    collector = ('java.lang:name=ParNew,type=GarbageCollector', 'java.lang:name=ConcurrentMarkSweep,type=GarbageCollector')
                    for coltype in collector:
                        beans = json.loads(lib.commonclient.httpget(__name__, storm_url + '/' + coltype))

                        lastgcinfo = beans['value']['LastGcInfo']['duration']
                        collectioncount = beans['value']['CollectionCount']
                        collectiontime = beans['value']['CollectionTime']
                        def push_metrics(preffix):
                            collectiontime_rate = rate.record_value_rate('storm_' + port + '_' + ''+preffix+'_collection_time', collectiontime, timestamp)

                            local_vars.append({'name': 'storm_' + port + '_' + '' + preffix + '_lastgcinfo', 'timestamp': timestamp, 'value': lastgcinfo, 'check_type': check_type})
                            local_vars.append({'name': 'storm_' + port + '_' + '' + preffix + '_collection_count', 'timestamp': timestamp, 'value': collectioncount, 'check_type': check_type})
                            local_vars.append({'name': 'storm_' + port + '_' + '' + preffix + '_collection_time', 'timestamp': timestamp, 'value': collectiontime_rate, 'check_type': check_type})


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
                            m_name = 'storm_' + port + '_' + 'g1_young_lastgcinfo'
                        local_vars.append({'name': m_name, 'timestamp': timestamp, 'value': v, 'check_type': check_type})

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
                                collectiontime_rate = rate.record_value_rate('storm_' + port + '_' + '' + rate_key, v, timestamp)
                                local_vars.append({'name': 'storm_' + port + '_' + 'g1' + type + vl.lower(), 'timestamp': timestamp, 'value': collectiontime_rate, 'chart_type': 'Rate', 'check_type': check_type})
                            if ky is 1:
                                value = j['value'][vl]
                                v = check_null(value)
                                local_vars.append({'name': 'storm_' + port + '_' + 'g1' + type + vl.lower(), 'timestamp': timestamp, 'value': v, 'check_type': check_type, 'reaction': -3})
            except Exception as e:
                lib.puylogger.print_message(__name__ + ' Error : ' + str(e) + ' ' + str(port))
                pass
        return local_vars

    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass


