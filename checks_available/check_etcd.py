import lib.record_rate
import lib.commonclient
import lib.getconfig
import lib.puylogger
import lib.basecheck

metrics = lib.getconfig.getparam('etcd', 'metrics')
check_type = 'etcd'
greps = ('sum', 'count', 'process')
reaction = 0

class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            data = lib.commonclient.httpget(__name__, metrics).splitlines()
            for c in data:
                if any(x in c for x in greps) and '#' not in c:
                    o = c.split()
                    if c.startswith('etcd_'):
                        self.local_vars.append({'name': o[0], 'timestamp': self.timestamp, 'value': float(o[1]), 'reaction': reaction})
                    else:
                        self.local_vars.append({'name': 'etcd_' + o[0], 'timestamp': self.timestamp, 'value': float(o[1]), 'reaction': reaction})
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass


