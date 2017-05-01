import lib.record_rate
import lib.pushdata
import lib.puylogger
import lib.jolostart
import urllib2
import os
import sys
import ConfigParser
import datetime
import socket
import json

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0] + '/conf/config.ini')
config.read(os.path.split(os.path.dirname(__file__))[0] + '/conf/java.ini')

hostname = socket.getfqdn()
jmxj_url = config.get('JMXJ', 'jmxj')

cluster_name = config.get('SelfConfig', 'cluster_name')
java = config.get('JMXJ', 'java')
juser = config.get('JMXJ', 'user')
jclass = config.get('JMXJ', 'class')
check_type = 'JMX'
reaction = -3

lib.jolostart.do_joloikia(java, juser, jclass)

def runcheck():
    try:
        data_dict = json.loads(urllib2.urlopen(jmxj_url + '/java.lang:type=GarbageCollector,name=*', timeout=5).read())
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

        sys.path.append(os.path.split(os.path.dirname(__file__))[0] + '/lib')
        jsondata = lib.pushdata.JonSon()
        jsondata.prepare_data()
        rate = lib.record_rate.ValueRate()
        timestamp = int(datetime.datetime.now().strftime("%s"))
        sys.path.append(os.path.split(os.path.dirname(__file__))[0] + '/lib')
        heam_mem = 'java.lang:type=Memory'
        jolo_url = urllib2.urlopen(jmxj_url + '/' + heam_mem, timeout=5).read()
        jolo_json = json.loads(jolo_url)
        jolo_keys = jolo_json['value']
        metr_name = ('used', 'committed', 'max')
        heap_type = ('NonHeapMemoryUsage', 'HeapMemoryUsage')
        for heap in heap_type:
            for metr in metr_name:
                if heap == 'NonHeapMemoryUsage':
                    key = 'jmxj_nonheap_' + metr
                    mon_values = jolo_keys[heap][metr]
                    if metr == 'used':
                        jsondata.gen_data(key, timestamp, mon_values, lib.pushdata.hostname, check_type, cluster_name)
                    else:
                        jsondata.gen_data(key, timestamp, mon_values, lib.pushdata.hostname, check_type, cluster_name, reaction)
                else:
                    key = 'jmxj_heap_' + metr
                    mon_values = jolo_keys[heap][metr]
                    if metr == 'used':
                        jsondata.gen_data(key, timestamp, mon_values, lib.pushdata.hostname, check_type, cluster_name)
                    else:
                        jsondata.gen_data(key, timestamp, mon_values, lib.pushdata.hostname, check_type, cluster_name, reaction)
        if CMS is True:
            collector = ('java.lang:name=ParNew,type=GarbageCollector', 'java.lang:name=ConcurrentMarkSweep,type=GarbageCollector')
            for coltype in collector:
                beans = json.loads(urllib2.urlopen(jmxj_url + '/' + coltype, timeout=5).read())
                if beans['value']['LastGcInfo']:
                    LastGcInfo = beans['value']['LastGcInfo']['duration']
                CollectionCount = beans['value']['CollectionCount']
                CollectionTime = beans['value']['CollectionTime']

                def push_metrics(preffix):
                    jsondata.gen_data('jmxj_' + preffix + '_CollectionCount', timestamp, CollectionCount, lib.pushdata.hostname, check_type, cluster_name)
                    CollectionTime_rate = rate.record_value_rate('jmxj_' + preffix + '_CollectionTime', CollectionTime, timestamp)
                    jsondata.gen_data('jmxj_' + preffix + '_CollectionTime', timestamp, CollectionTime_rate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')
                    if 'LastGcInfo' in locals():
                        jsondata.gen_data('jmxj_' + preffix + '_LastGcInfo', timestamp, LastGcInfo, lib.pushdata.hostname, check_type, cluster_name)

                if coltype == 'java.lang:name=ConcurrentMarkSweep,type=GarbageCollector':
                    push_metrics(preffix='CMS')
                if coltype == 'java.lang:name=ParNew,type=GarbageCollector':
                    push_metrics(preffix='ParNew')

        if G1 is True:
            gc_g1 = ('/java.lang:name=G1%20Old%20Generation,type=GarbageCollector', '/java.lang:name=G1%20Young%20Generation,type=GarbageCollector')

            def check_null(value):
                if value is None:
                    value = 0
                    return value
                else:
                    return value

            for k, v in enumerate(gc_g1):
                j = json.load(urllib2.urlopen(jmxj_url + v, timeout=5))
                name = 'LastGcInfo'
                if k is 0:
                    try:
                        value = j['value'][name]['duration']
                        v = check_null(value)
                    except:
                        v = 0
                        pass
                    m_name = 'jmxj_G1_old_LastGcInfo'
                if k is 1:
                    value = j['value'][name]['duration']
                    v = check_null(value)
                    m_name = 'jmxj_G1_young_LastGcInfo'
                jsondata.gen_data(m_name, timestamp, v, lib.pushdata.hostname, check_type, cluster_name)

            metr_keys = ('CollectionTime', 'CollectionCount')
            for k, v in enumerate(gc_g1):
                j = json.load(urllib2.urlopen(jmxj_url + v, timeout=5))
                if k is 0:
                    type = '_old_'
                if k is 1:
                    type = '_young_'
                for ky, vl in enumerate(metr_keys):
                    if ky is 0:
                        value = j['value'][vl]
                        v = check_null(value)
                        rate_key = vl + type
                        CollectionTime_rate = rate.record_value_rate('jmxj_' + rate_key, v, timestamp)
                        jsondata.gen_data('jmxj_G1' + type + vl, timestamp, CollectionTime_rate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')
                    if ky is 1:
                        value = j['value'][vl]
                        v = check_null(value)
                        jsondata.gen_data('jmxj_G1' + type + vl, timestamp, v, lib.pushdata.hostname, check_type, cluster_name)
        jolo_threads = 'java.lang:type=Threading'
        jolo_turl = urllib2.urlopen(jmxj_url + '/' + jolo_threads, timeout=5).read()
        jolo_tjson = json.loads(jolo_turl)
        thread_metrics = ('TotalStartedThreadCount', 'PeakThreadCount', 'ThreadCount', 'DaemonThreadCount')
        for thread_metric in thread_metrics:
            name = 'jmxj_' + thread_metric
            vlor = jolo_tjson['value'][thread_metric]
            jsondata.gen_data(name, timestamp, vlor, lib.pushdata.hostname, check_type, cluster_name)

        jsondata.put_json()

    except Exception as e:
        lib.pushdata.print_error(__name__, (e))
        try:
            lib.jolostart.do_joloikia(java, juser, jclass)
        except Exception as jolo:
            lib.pushdata.print_error(__name__, (jolo))
        pass


