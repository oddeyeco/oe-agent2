import lib.puylogger
import lib.record_rate
import lib.getconfig
import lib.commonclient
import lib.basecheck
import json
import socket

couchdb_url = lib.getconfig.getparam('CouchDB2', 'stats')
couchdb_auth = lib.getconfig.getparam('CouchDB2', 'user')+':'+lib.getconfig.getparam('CouchDB2', 'pass')
curl_auth = lib.getconfig.getparam('CouchDB2', 'auth')
detailed = lib.getconfig.getparam('CouchDB2', 'detailed')

cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_type = 'couchdb'

codes = ['200','201','202','204','206','301','302','304','400','401','403','404','405','406','409','412','413','414','415','416','417','500','501','503']
methods = ['COPY', 'DELETE', 'GET', 'HEAD', 'OPTIONS', 'POST', 'PUT']
dbops = ['database_writes', 'database_reads', 'document_inserts', 'document_writes']
httpd = ['bulk_requests', 'requests', 'temporary_view_reads', 'view_reads']

class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:

            memberslist = json.loads(lib.commonclient.httpget(__name__, couchdb_url + '/_membership', couchdb_auth))


            for couch in memberslist['all_nodes']:
                try:
                    nodename = socket.gethostbyaddr(couch.split('@')[1])[0]
                except:
                    nodename = couch.split('@')[1]

                metrics = json.loads(lib.commonclient.httpget(__name__, couchdb_url + '/_node/' + couch + '/_stats', couchdb_auth))

                for dbop in dbops:
                    reqrate = self.rate.record_value_rate(nodename + '_couchdb_' + dbop, metrics['couchdb'][dbop]['value'], self.timestamp)
                    self.local_vars.append({'name': 'couchdb_' + dbop, 'host': nodename, 'timestamp': self.timestamp, 'value': int(reqrate), 'check_type': check_type})

                for h in httpd:
                    reqrate = self.rate.record_value_rate(nodename + '_couchdb_' + h, metrics['couchdb']['httpd'][h]['value'], self.timestamp)
                    self.local_vars.append({'name': 'couchdb_' + h, 'host': nodename, 'timestamp': self.timestamp, 'value': int(reqrate), 'check_type': check_type})

                if detailed:
                    for m in methods:
                        reqrate = self.rate.record_value_rate(nodename + '_couchdb_' + m, metrics['couchdb']['httpd_request_methods'][m]['value'], self.timestamp)
                        self.local_vars.append({'name': 'couchdb_requests_methods', 'host': nodename, 'timestamp': self.timestamp, 'value': int(reqrate), 'check_type': check_type, 'extra_tag': {'method': m.lower()}})
                    for c in codes:
                        reqrate = self.rate.record_value_rate(nodename + '_couchdb_' + str(c), metrics['couchdb']['httpd_status_codes'][c]['value'], self.timestamp)
                        self.local_vars.append({'name': 'couchdb_status_codes', 'host': nodename, 'timestamp': self.timestamp, 'value': int(reqrate), 'check_type': check_type, 'extra_tag': {'method': c}})


        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
    
    
    
