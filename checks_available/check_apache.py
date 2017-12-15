import lib.getconfig
import lib.basecheck
import lib.record_rate
import lib.puylogger
import lib.commonclient


apache_url = lib.getconfig.getparam('Apache', 'url')

apache_auth = lib.getconfig.getparam('Apache', 'user')+':'+lib.getconfig.getparam('Apache', 'pass')
curl_auth = lib.getconfig.getparam('Apache', 'auth')
check_type = 'apache'

class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            if curl_auth is True:
                data = lib.commonclient.httpget(__name__, apache_url, apache_auth)
            else:
                data = lib.commonclient.httpget(__name__, apache_url)

            metrics_rated = ('Total Accesses', 'Total kBytes')
            metrics_stuck = ('ReqPerSec', 'BytesPerSec', 'BytesPerReq', 'BusyWorkers', 'IdleWorkers')
            for line in data.split('\n'):
                for searchitem in  metrics_stuck:
                    if searchitem in line:
                        key = line.split(' ')[0].replace(':', '')
                        value = line.split(' ')[1]
                        self.local_vars.append({'name': 'apache_'+key.lower(), 'timestamp': self.timestamp, 'value': value, 'check_type': check_type})
                for searchitem in  metrics_rated:
                    reaction = 0
                    if searchitem in line:
                        key = line.split(' ')[0]+line.split(' ')[1].replace(':', '')
                        value = line.split(' ')[2]
                        value_rate = self.rate.record_value_rate(key, value, self.timestamp)
                        self.local_vars.append({'name': 'apache_' + key.lower(), 'timestamp': self.timestamp, 'value': value_rate, 'check_type': check_type, 'chart_type': 'Rate'})

        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass


