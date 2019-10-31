import lib.record_rate
import lib.getconfig
import lib.commonclient
import lib.puylogger
import lib.basecheck

haproxy_url = lib.getconfig.getparam('HAProxy', 'url')
haproxy_auth = lib.getconfig.getparam('HAProxy', 'user')+':'+lib.getconfig.getparam('HAProxy', 'pass')
curl_auth = lib.getconfig.getparam('HAProxy', 'auth')
check_type = 'haproxy'


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            if curl_auth is True:
                t = lib.commonclient.httpget(__name__, haproxy_url, haproxy_auth)
            else:
                t = lib.commonclient.httpget(__name__, haproxy_url)
            for line in t.split('\n'):
                        ddd = line.split(',')
                        if 'pxname,svname' not in line and len(ddd) > 1:
                            if ddd[1] == 'FRONTEND':
                                self.local_vars.append({'name': 'haproxy_connrate', 'timestamp': self.timestamp, 'value': ddd[33], 'check_type': check_type, 'chart_type': 'Rate', 'extra_tag': {'frontend': ddd[0]}})
                                self.local_vars.append({'name': 'haproxy_sessions', 'timestamp': self.timestamp, 'value': ddd[4], 'check_type': check_type, 'extra_tag': {'frontend': ddd[0]}})
                            elif ddd[1] == 'BACKEND':
                                self.local_vars.append({'name': 'haproxy_queue', 'timestamp': self.timestamp, 'value': ddd[2], 'check_type': check_type, 'extra_tag': {'backend': ddd[0]}})
                                self.local_vars.append({'name': 'haproxy_connrate', 'timestamp': self.timestamp, 'value': ddd[33], 'check_type': check_type, 'chart_type': 'Rate', 'extra_tag': {'backend': ddd[0]}})
                                self.local_vars.append({'name': 'haproxy_sessions', 'timestamp': self.timestamp, 'value': ddd[4], 'check_type': check_type, 'extra_tag': {'backend': ddd[0]}})
                            else:
                                upstream = ddd[1]
                                self.local_vars.append({'name': 'haproxy_queue', 'timestamp': self.timestamp, 'value': ddd[2], 'check_type': check_type, 'extra_tag': {'upstream': upstream}})
                                self.local_vars.append({'name': 'haproxy_connrate', 'timestamp': self.timestamp, 'value': ddd[33], 'check_type': check_type, 'chart_type': 'Rate', 'extra_tag': {'upstream': upstream}})
                                self.local_vars.append({'name': 'haproxy_sessions', 'timestamp': self.timestamp, 'value': ddd[4], 'check_type': check_type, 'extra_tag': {'upstream': upstream}})
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass