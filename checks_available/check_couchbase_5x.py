import lib.record_rate
import lib.puylogger
import lib.getconfig
import lib.commonclient
import lib.basecheck
import json
import socket

couchbase_url = lib.getconfig.getparam('CouchBase5x', 'stats')
buckets = lib.getconfig.getparam('CouchBase5x', 'buckets').replace(' ', '').split(',')
check_type = 'couchbase'

couchbase_auth = lib.getconfig.getparam('CouchBase5x', 'user')+':'+lib.getconfig.getparam('CouchBase5x', 'pass')
curl_auth = lib.getconfig.getparam('CouchBase5x', 'auth')

stats = ('cmd_get', 'couch_docs_data_size', 'curr_items', 'curr_items_tot', 'ep_bg_fetched', 'get_hits', 'mem_used', 'ops', 'vb_replica_curr_items')
basicstats = ('quotaPercentUsed', 'opsPerSec', 'itemCount', 'memUsed')


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            for bucket in buckets:

                if curl_auth is True:
                    stats_json = json.loads(lib.commonclient.httpget(__name__, couchbase_url + '/' + bucket, couchbase_auth))
                else:
                    stats_json = json.loads(lib.commonclient.httpget(__name__, couchbase_url + '/' + bucket))

                for x in range(0, len(stats_json['nodes'])):
                    longname = stats_json['nodes'][x]['hostname'].split(':')[0]

                    try:
                        nodename=socket.gethostbyaddr(longname)[0]
                    except:
                        nodename=longname

                    for stat in stats:
                        # name = 'couchbase_' + longname + '_' + stat
                        name = 'couchbase_' + stat
                        value = float(stats_json['nodes'][x]['interestingStats'][stat])
                        self.local_vars.append({'name': name.lower(), 'host': nodename, 'timestamp': self.timestamp, 'value': value, 'check_type': check_type, 'extra_tag': {'bucket': bucket}})
                for bstat in basicstats:
                    name = 'couchbase_clusterwide_' + bstat
                    value = float(stats_json['basicStats'][bstat])
                    self.local_vars.append({'name': name.lower(), 'timestamp': self.timestamp, 'value': value, 'check_type': check_type, 'extra_tag': {'bucket': bucket}})

        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass