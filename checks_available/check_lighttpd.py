import lib.record_rate
import lib.commonclient
import lib.getconfig
import lib.puylogger
import lib.basecheck

lighttpd_url = lib.getconfig.getparam('Lighttpd', 'address') + lib.getconfig.getparam('Lighttpd', 'stats')
lighttpd_auth = lib.getconfig.getparam('Lighttpd', 'user')+':'+lib.getconfig.getparam('Lighttpd', 'pass')
curl_auth = lib.getconfig.getparam('Lighttpd', 'auth')
check_type = 'lighttpd'

rateds = ('accesses', 'kbytes')
stacks = ('busyservers', 'idleservers')

class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:

            if curl_auth is True:
                data = lib.commonclient.httpget(__name__, lighttpd_url, lighttpd_auth).splitlines()
            else:
                data = lib.commonclient.httpget(__name__, lighttpd_url).splitlines()
            for line in data:
                if 'Scoreboard' not in line:
                    d = line.replace(' ', '').replace('Total', '').lower().split(':')
                    if any(s in d for s in rateds):
                        r = self.rate.record_value_rate('lighttpd_'+ d[0], d[1], self.timestamp)
                        self.local_vars.append({'name': 'lighttpd_'+ d[0], 'timestamp': self.timestamp, 'value': r, 'check_type': check_type, 'chart_type': 'Rate'})
                    if any(s in d for s in stacks):
                        self.local_vars.append({'name': 'lighttpd_' + d[0], 'timestamp': self.timestamp, 'value': d[1], 'check_type': check_type})

        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass


