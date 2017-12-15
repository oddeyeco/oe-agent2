import lib.record_rate
import lib.puylogger
import lib.getconfig
import lib.commonclient
import lib.basecheck
import json
import re

couchbase_url = lib.getconfig.getparam('CouchBase', 'stats')
buckets = lib.getconfig.getparam('CouchBase', 'buckets').replace(' ', '').split(',')
check_type = 'couchbase'

stats = ('cmd_get', 'couch_docs_data_size', 'curr_items', 'curr_items_tot', 'ep_bg_fetched', 'get_hits', 'mem_used', 'ops', 'vb_replica_curr_items')
basicstats = ('quotaPercentUsed', 'opsPerSec', 'hitRatio', 'itemCount', 'memUsed')


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            for bucket in buckets:
                stats_json = json.loads(lib.commonclient.httpget(__name__, couchbase_url + '/' + bucket))

                for x in range(0, len(stats_json['nodes'])):
                    longname = stats_json['nodes'][x]['hostname'].split(':')[0]

                    def is_valid_hostname(hostname):
                        if len(hostname) > 255:
                            return False
                        if hostname[-1] == ".":
                            hostname = hostname[:-1]
                        allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
                        return all(allowed.match(x) for x in hostname.split("."))

                    if is_valid_hostname(longname):
                        nodename = longname.split('.')[0]
                    else:
                        nodename = longname.replace('.', '_')

                    for stat in stats:
                        name = 'couchbase_' + nodename + '_' + stat
                        value = float(stats_json['nodes'][x]['interestingStats'][stat])
                        self.local_vars.append({'name': name.lower(), 'timestamp': self.timestamp, 'value': value, 'check_type': check_type})

                for bstat in basicstats:
                    name = 'couchbase_clusterwide_' + bstat
                    value = float(stats_json['basicStats'][bstat])
                    self.local_vars.append({'name': name.lower(), 'timestamp': self.timestamp, 'value': value, 'check_type': check_type})

        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass