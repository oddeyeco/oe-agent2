import lib.record_rate
import lib.commonclient
import lib.getconfig
import lib.puylogger
import lib.basecheck

metrics = lib.getconfig.getparam('coredns', 'metrics')
check_type = 'coredns'
reaction = 0

class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            data = lib.commonclient.httpget(__name__, metrics).splitlines()
            for c in data:
                if '{' not in c and '#' not in c:
                    o = c.split()
                    if c.startswith('coredns_'):
                        self.local_vars.append({'name': o[0], 'timestamp': self.timestamp, 'value': float(o[1]), 'reaction': reaction})
                    else:
                        self.local_vars.append({'name': 'coredns_' + o[0], 'timestamp': self.timestamp, 'value': float(o[1]), 'reaction': reaction})
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass


