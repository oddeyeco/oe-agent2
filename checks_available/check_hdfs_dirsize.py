import lib.record_rate
import lib.getconfig
import lib.commonclient
import lib.puylogger
import lib.basecheck
import json
import re

namenodes = lib.getconfig.getparam('HDFS-Directory', 'namenodes').replace(' ', '').split(',')
hadoop_folders = lib.getconfig.getparam('HDFS-Directory', 'folders').replace(' ', '').split(',')
check_type = 'hdfs'

def getactivenn():
    for oo in (namenodes):

        candidate = lib.commonclient.httpget(__name__, oo + "/dfshealth.jsp")
        try:
            if re.search(r"active", candidate):
                return oo + '/webhdfs/v1'
        except Exception as foo:
            lib.puylogger.print_message(str(foo))

    return None


class Checkex:
    nn = getactivenn()

class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            statuses = ['length', 'directoryCount', 'spaceConsumed', 'fileCount']
            for hdir in hadoop_folders:
                hadoop_namenode_stats = json.loads(lib.commonclient.httpget(__name__, Checkex.nn + hdir + '?op=GETCONTENTSUMMARY'))
                for o in statuses:
                    self.local_vars.append({'name': 'hdfs_dir_' + o.lower(), 'timestamp': self.timestamp, 'value': hadoop_namenode_stats['ContentSummary'][o],
                                            'reaction': -3, 'extra_tag': {'hadoop_dir': hdir.strip('/').replace('/', '_')}})
        except Exception as omg:
            Checkex.nn = getactivenn()
