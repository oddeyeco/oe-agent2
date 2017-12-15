import lib.record_rate
import lib.commonclient
import lib.getconfig
import lib.puylogger
import lib.basecheck

phpfpm_url = lib.getconfig.getparam('PhpFPM', 'address') + lib.getconfig.getparam('PhpFPM', 'stats')
phpfpm_auth = lib.getconfig.getparam('PhpFPM', 'user')+':'+lib.getconfig.getparam('PhpFPM', 'pass')
curl_auth = lib.getconfig.getparam('PhpFPM', 'auth')
check_type = 'php-fpm'


class Check(lib.basecheck.CheckBase):

    def precheck(self):

        try:
            if curl_auth is True:
                data = lib.commonclient.httpget(__name__, phpfpm_url, phpfpm_auth)
            else:
                data = lib.commonclient.httpget(__name__, phpfpm_url)

            connections = data.splitlines()[4].split(':')[1].replace(" ", "")
            proc_idle = data.splitlines()[8].split(':')[1].replace(" ", "")
            proc_active = data.splitlines()[9].split(':')[1].replace(" ", "")
            proc_total = data.splitlines()[10].split(':')[1].replace(" ", "")
            max_active = data.splitlines()[11].split(':')[1].replace(" ", "")
            max_children = data.splitlines()[12].split(':')[1].replace(" ", "")
            slow_request = data.splitlines()[13].split(':')[1].replace(" ", "")
            rate = lib.record_rate.ValueRate()
            conns_per_sec = rate.record_value_rate('phpfpm_connections', connections, self.timestamp)

            self.local_vars.append({'name': 'phpfpm_conns_per_sec', 'timestamp': self.timestamp, 'value': conns_per_sec, 'check_type': check_type, 'chart_type': 'Rate'})
            self.local_vars.append({'name': 'phpfpm_proc_idle', 'timestamp': self.timestamp, 'value': proc_idle, 'check_type': check_type})
            self.local_vars.append({'name': 'phpfpm_proc_active', 'timestamp': self.timestamp, 'value': proc_active, 'check_type': check_type})
            self.local_vars.append({'name': 'phpfpm_proc_total', 'timestamp': self.timestamp, 'value': proc_total, 'check_type': check_type})
            self.local_vars.append({'name': 'phpfpm_max_active', 'timestamp': self.timestamp, 'value': max_active, 'check_type': check_type})
            self.local_vars.append({'name': 'phpfpm_max_children', 'timestamp': self.timestamp, 'value': max_children, 'check_type': check_type})
            self.local_vars.append({'name': 'phpfpm_slow_request', 'timestamp': self.timestamp, 'value': slow_request, 'check_type': check_type})

        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass


