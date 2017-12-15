import lib.record_rate
import lib.commonclient
import lib.getconfig
import lib.puylogger
import lib.basecheck

nginx_url = lib.getconfig.getparam('NginX', 'address') + lib.getconfig.getparam('NginX', 'stats')
nginx_auth = lib.getconfig.getparam('NginX', 'user')+':'+lib.getconfig.getparam('NginX', 'pass')
curl_auth = lib.getconfig.getparam('NginX', 'auth')
check_type = 'nginx'


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
    
            if curl_auth is True:
                data = lib.commonclient.httpget(__name__, nginx_url, nginx_auth)
            else:
                data = lib.commonclient.httpget(__name__, nginx_url)
            connections = data.splitlines()[0].split(' ')[2]
            requests = data.splitlines()[2].split(' ')[3]
            handled = data.splitlines()[2].split(' ')[2]
            accept = data.splitlines()[2].split(' ')[1]
            reading = data.splitlines()[3].split(' ')[1]
            writing = data.splitlines()[3].split(' ')[3]
            waiting = data.splitlines()[3].split(' ')[5]
            reqrate = self.rate.record_value_rate('nginx_requests', requests, self.timestamp)
            handelerate = self.rate.record_value_rate('nginx_handled', handled, self.timestamp)
            acceptrate = self.rate.record_value_rate('nginx_accept', accept, self.timestamp)
    
            self.local_vars.append({'name': 'nginx_connections', 'timestamp': self.timestamp, 'value': connections, 'check_type': check_type})
            self.local_vars.append({'name': 'nginx_requests', 'timestamp': self.timestamp, 'value': reqrate, 'check_type': check_type, 'chart_type': 'Rate'})
            self.local_vars.append({'name': 'nginx_handled', 'timestamp': self.timestamp, 'value': handelerate, 'check_type': check_type, 'chart_type': 'Rate'})
            self.local_vars.append({'name': 'nginx_accept', 'timestamp': self.timestamp, 'value': acceptrate, 'check_type': check_type, 'chart_type': 'Rate'})
            self.local_vars.append({'name': 'nginx_reading', 'timestamp': self.timestamp, 'value': reading, 'check_type': check_type})
            self.local_vars.append({'name': 'nginx_writing', 'timestamp': self.timestamp, 'value': writing, 'check_type': check_type})
            self.local_vars.append({'name': 'nginx_waiting', 'timestamp': self.timestamp, 'value': waiting, 'check_type': check_type})
    
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
    
    
