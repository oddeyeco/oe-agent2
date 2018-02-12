import lib.record_rate
import lib.puylogger
import lib.record_rate
import lib.getconfig
import lib.commonclient
import lib.basecheck
import json



solr_url = lib.getconfig.getparam('Solr', 'stats')
check_type = 'solr'


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            stats_json = json.loads(lib.commonclient.httpget(__name__, solr_url))
            requests = ('delete', 'get', 'head', 'move', 'options', 'other', 'put', 'trace')
            responses = ('1xx', '2xx', '3xx', '4xx', '5xx')
            heapstats = ('committed', 'init', 'max', 'used')
            sothreads = ('threads.count', 'threads.daemon.count')
            garbage = ('gc.ConcurrentMarkSweep.count', 'gc.ConcurrentMarkSweep.time', 'gc.ParNew.count', 'gc.ParNew.time',
                   'gc.G1-Old-Generation.count','gc.G1-Old-Generation.time' ,'gc.G1-Young-Generation.count', 'gc.G1-Young-Generation.time')
            for rqst in requests:
                rqst_name = 'org.eclipse.jetty.server.handler.DefaultHandler.' + rqst + '-requests'
                rqvalue= stats_json['metrics']['solr.jetty'][rqst_name]['count']
                csrate = self.rate.record_value_rate('slr_'+rqst, rqvalue, self.timestamp)
                self.local_vars.append({'name': 'solr_' + rqst + '_requests', 'timestamp': self.timestamp, 'value': csrate, 'check_type': check_type, 'chart_type': 'Rate'})

            total_requests = 'org.eclipse.jetty.server.handler.DefaultHandler.requests'
            trv = stats_json['metrics']['solr.jetty'][total_requests]['count']
            rqrate = self.rate.record_value_rate('slr_total_requests', trv, self.timestamp)
            self.local_vars.append({'name': 'solr_requests_all', 'timestamp': self.timestamp, 'value': rqrate, 'check_type': check_type, 'chart_type': 'Rate'})

            for resp in responses:
                resp_name = 'org.eclipse.jetty.server.handler.DefaultHandler.' + resp + '-responses'
                csvalue = stats_json['metrics']['solr.jetty'][resp_name]['count']
                csrate = self.rate.record_value_rate('slr_'+resp, csvalue, self.timestamp)
                self.local_vars.append({'name': 'solr_' + resp + '_responses', 'timestamp': self.timestamp, 'value': csrate, 'check_type': check_type, 'chart_type': 'Rate'})

            for hu in heapstats:
                hu_name = 'memory.heap.' + hu
                huvalue = stats_json['metrics']['solr.jvm'][hu_name]
                self.local_vars.append({'name': 'solr_heap_' + hu, 'timestamp': self.timestamp, 'value': huvalue, 'check_type': check_type})

            for nohu in heapstats:
                nohu_name = 'memory.non-heap.' + nohu
                nohuvalue = stats_json['metrics']['solr.jvm'][nohu_name]
                self.local_vars.append({'name': 'solr_non_heap_' + nohu, 'timestamp': self.timestamp, 'value': nohuvalue, 'check_type': check_type})

            for tr in sothreads:
                trvalue = stats_json['metrics']['solr.jvm'][tr]
                self.local_vars.append({'name': 'solr_' + tr.replace('.', '_').replace('_count', ''), 'timestamp': self.timestamp, 'value': trvalue, 'check_type': check_type})

            for gc in garbage:
                if gc in stats_json['metrics']['solr.jvm']:
                    gcvalue = stats_json['metrics']['solr.jvm'][gc]
                    self.local_vars.append({'name': 'solr_' + gc.replace('.', '_').replace('ConcurrentMarkSweep', 'CMS').lower(), 'timestamp': self.timestamp, 'value': gcvalue, 'check_type': check_type})
    
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
    
    
    
