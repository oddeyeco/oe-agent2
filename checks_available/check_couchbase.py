import lib.record_rate
import lib.puylogger
import lib.getconfig
import lib.pushdata
import lib.commonclient
import datetime
import json
import re

couchbase_url = lib.getconfig.getparam('CouchBase', 'stats')
buckets = lib.getconfig.getparam('CouchBase', 'buckets').replace(' ', '').split(',')

cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_type = 'couchbase'

# timestamp = int(datetime.datetime.now().strftime("%s"))

stats = ('cmd_get', 'couch_docs_data_size', 'curr_items', 'curr_items_tot', 'ep_bg_fetched', 'get_hits', 'mem_used', 'ops', 'vb_replica_curr_items')
basicstats = ('quotaPercentUsed', 'opsPerSec', 'hitRatio', 'itemCount', 'memUsed')


def runcheck():
    try:
        timestamp = int(datetime.datetime.now().strftime("%s"))
        for bucket in buckets:
            jsondata=lib.pushdata.JonSon()
            jsondata.prepare_data()
            stats_json = json.loads(lib.commonclient.httpget(__name__, couchbase_url + '/' + bucket))

            for x in range(0, len(stats_json['nodes'])):
                longname=stats_json['nodes'][x]['hostname'].split(':')[0]

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
                    jsondata.gen_data(name.lower(), timestamp, value, lib.pushdata.hostname, check_type, cluster_name)

            for bstat in basicstats:
                name = 'couchbase_clusterwide_' + bstat
                value = float(stats_json['basicStats'][bstat])
                jsondata.gen_data(name.lower(), timestamp, value, lib.pushdata.hostname, check_type, cluster_name)

            jsondata.put_json()
    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass