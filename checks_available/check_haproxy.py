import lib.record_rate
import lib.getconfig
import lib.commonclient
import lib.puylogger
import datetime


haproxy_url = lib.getconfig.getparam('HAProxy', 'url')
haproxy_auth = lib.getconfig.getparam('HAProxy', 'user')+':'+lib.getconfig.getparam('HAProxy', 'pass')
curl_auth = lib.getconfig.getparam('HAProxy', 'auth')
cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
haproxy_upstream = lib.getconfig.getparam('HAProxy', 'upstream').split(',')
check_type = 'haproxy'

def runcheck():
    local_vars = []
    try:
        if curl_auth is True:
            t = lib.commonclient.httpget(__name__, haproxy_url, haproxy_auth)
        else:
            t = lib.commonclient.httpget(__name__, haproxy_url)
        lazy_totals = ("FRONTEND", "BACKEND")
        timestamp = int(datetime.datetime.now().strftime("%s"))
        for line in t.split('\n'):
            for application in haproxy_upstream:
                if application in line:
                    if not any(s in line for s in lazy_totals):
                        upstream = line.split(',')[1]
                        sessions = line.split(',')[4]
                        connrate = line.split(',')[33]
                        local_vars.append({'name': 'haproxy_connrate_' + upstream, 'timestamp': timestamp, 'value': connrate, 'check_type': check_type, 'chart_type': 'Rate'})
                        local_vars.append({'name': 'haproxy_sessions_' + upstream, 'timestamp': timestamp, 'value': sessions, 'check_type': check_type})
        return local_vars
    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass


