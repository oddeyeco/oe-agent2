import lib.record_rate
import lib.pushdata
import urllib2
import os, sys
import ConfigParser
import datetime
import socket
import json
import lib.puylogger
import lib.record_rate


config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/bigdata.ini')


solr_url = config.get('Solr', 'stats')

hostname = socket.getfqdn()
cluster_name = config.get('SelfConfig', 'cluster_name')
check_type = 'solr'

timestamp = int(datetime.datetime.now().strftime("%s"))

def runcheck():
    try:
        stats = urllib2.urlopen(solr_url, timeout=5).read()
        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        stats_json = json.loads(stats)

        jsondata = lib.pushdata.JonSon()
        jsondata.prepare_data()
        rate = lib.record_rate.ValueRate()
        timestamp = int(datetime.datetime.now().strftime("%s"))

        requests = ('active', 'delete', 'get', 'head', 'move', 'options', 'other', 'put', 'trace')
        responses = ('1xx', '2xx', '3xx', '4xx', '5xx')
        heapstats = ('committed', 'init', 'max', 'used')
        sothreads = ('threads.count', 'threads.daemon.count')
        garbage = ('gc.ConcurrentMarkSweep.count', 'gc.ConcurrentMarkSweep.time', 'gc.ParNew.count', 'gc.ParNew.time',
               'gc.G1-Old-Generation.count','gc.G1-Old-Generation.time' ,'gc.G1-Young-Generation.count', 'gc.G1-Young-Generation.time')
        for rqst in requests:
            rqst_name = 'org.eclipse.jetty.server.handler.DefaultHandler.' + rqst + '-requests'
            rqvalue= stats_json['metrics'][1][rqst_name]['count']
            csrate = rate.record_value_rate('slr_'+rqst, rqvalue, timestamp)
            jsondata.gen_data('solr_' + rqst + '_requests', timestamp, csrate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')

        total_requests = 'org.eclipse.jetty.server.handler.DefaultHandler.requests'
        trv = stats_json['metrics'][1][total_requests]['count']
        rqrate = rate.record_value_rate('slr_total_requests', trv, timestamp)
        jsondata.gen_data('solr_requests_all', timestamp, rqrate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')

        for resp in responses:
            resp_name = 'org.eclipse.jetty.server.handler.DefaultHandler.' + resp + '-responses'
            csvalue= stats_json['metrics'][1][resp_name]['count']
            csrate = rate.record_value_rate('slr_'+resp, csvalue, timestamp)
            jsondata.gen_data('solr_' + resp + '_responses', timestamp, csrate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')

        for hu in heapstats:
            hu_name = 'memory.heap.' + hu
            huvalue= stats_json['metrics'][3][hu_name]['value']
            jsondata.gen_data('solr_heap_' + hu, timestamp, huvalue, lib.pushdata.hostname, check_type, cluster_name)

        for nohu in heapstats:
            nohu_name = 'memory.non-heap.' + nohu
            nohuvalue= stats_json['metrics'][3][nohu_name]['value']
            jsondata.gen_data('solr_non_heap_' + nohu, timestamp, nohuvalue, lib.pushdata.hostname, check_type, cluster_name)

        for tr in sothreads:
            trvalue= stats_json['metrics'][3][tr]['value']
            jsondata.gen_data('solr_' + tr.replace('.', '_').replace('_count', ''), timestamp, trvalue, lib.pushdata.hostname, check_type, cluster_name)

        for gc in garbage:
            if gc in stats_json['metrics'][3]:
                gcvalue=stats_json['metrics'][3][tr]['value']
                jsondata.gen_data('solr_' + gc.replace('.', '_').replace('ConcurrentMarkSweep', 'CMS'), timestamp, gcvalue, lib.pushdata.hostname, check_type, cluster_name)

        jsondata.put_json()
    except Exception as e:
        lib.pushdata.print_error(__name__, (e))
        pass



