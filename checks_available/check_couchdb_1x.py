import lib.puylogger
import lib.record_rate
import lib.getconfig
import lib.commonclient
import lib.basecheck
import json


couchdb_url = lib.getconfig.getparam('CouchDB', 'stats')

cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_type = 'couchdb'

class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            stats_json = json.loads(lib.commonclient.httpget(__name__, couchdb_url))
            sections = ('couchdb', 'httpd_request_methods', 'httpd_status_codes', 'httpd')
            couchdb_stats = ('auth_cache_misses', 'database_writes', 'open_databases', 'auth_cache_hits', 'request_time', 'database_reads', 'open_os_files')
            httpd_methods = ('GET', 'PUT', 'COPY', 'DELETE', 'POST', 'HEAD')
            httpd_codes = ('200', '201', '202', '301', '304', '400', '401', '403', '404', '405', '409', '412', '500')
            httpd_stats = ('clients_requesting_changes', 'temporary_view_reads', 'requests', 'bulk_requests', 'view_reads')
    
            for cs in couchdb_stats:
                if stats_json[sections[0]][cs]['current'] is not None:
                    csvalue = stats_json[sections[0]][cs]['current']
                    csrate = self.rate.record_value_rate('couch_'+cs, csvalue, self.timestamp)
                    self.local_vars.append({'name': 'couchdb_' + cs, 'timestamp': self.timestamp, 'value': csrate, 'check_type': check_type, 'chart_type': 'Rate'})
    
            for hm in httpd_methods:
                if stats_json[sections[1]][hm]['current'] is not None:
                    hmrate = self.rate.record_value_rate('couch_' + hm, stats_json[sections[1]][hm]['current'], self.timestamp)
                    self.local_vars.append({'name': 'couchdb_' + hm.lower(), 'timestamp': self.timestamp, 'value': hmrate, 'check_type': check_type, 'chart_type': 'Rate'})
    
            for hc in httpd_codes:
                hc = str(hc)
                if stats_json[sections[2]][hc]['current'] is not None:
                    hcrate = self.rate.record_value_rate('couch_' + hc, stats_json[sections[2]][hc]['current'], self.timestamp)
                    self.local_vars.append({'name': 'couchdb_' + hc.lower(), 'timestamp': self.timestamp, 'value': hcrate, 'check_type': check_type, 'chart_type': 'Rate'})
    
            for hs in httpd_stats:
                if stats_json[sections[3]][hs]['current'] is not None:
                    hsrate = self.rate.record_value_rate('couch_' + hs, stats_json[sections[3]][hs]['current'], self.timestamp)
                    self.local_vars.append({'name': 'couchdb_' + hs.lower(), 'timestamp': self.timestamp, 'value': hsrate, 'check_type': check_type, 'chart_type': 'Rate'})
    
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
    
    
    
