import lib.record_rate
import lib.commonclient
import lib.getconfig
import lib.puylogger
import datetime

nginx_url = lib.getconfig.getparam('NginX', 'address') + lib.getconfig.getparam('NginX', 'stats')
nginx_auth = lib.getconfig.getparam('NginX', 'user')+':'+lib.getconfig.getparam('NginX', 'pass')
curl_auth = lib.getconfig.getparam('NginX', 'auth')
cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_type = 'nginx'


def runcheck():
    local_vars = []
    try:

        if curl_auth is True:
            data = lib.commonclient.httpget(__name__, nginx_url, nginx_auth)
        else:
            data = lib.commonclient.httpget(__name__, nginx_url)
        rate = lib.record_rate.ValueRate()

        timestamp = int(datetime.datetime.now().strftime("%s"))
        connections = data.splitlines()[0].split(' ')[2]
        requests = data.splitlines()[2].split(' ')[3]
        handled = data.splitlines()[2].split(' ')[2]
        accept = data.splitlines()[2].split(' ')[1]
        reading = data.splitlines()[3].split(' ')[1]
        writing = data.splitlines()[3].split(' ')[3]
        waiting = data.splitlines()[3].split(' ')[5]
        reqrate = rate.record_value_rate('nginx_requests', requests, timestamp)
        handelerate = rate.record_value_rate('nginx_handled', handled, timestamp)
        acceptrate = rate.record_value_rate('nginx_accept', accept, timestamp)

        local_vars.append({'name': 'nginx_connections', 'timestamp': timestamp, 'value': connections, 'check_type': check_type})
        local_vars.append({'name': 'nginx_requests', 'timestamp': timestamp, 'value': reqrate, 'check_type': check_type, 'chart_type': 'Rate'})
        local_vars.append({'name': 'nginx_handled', 'timestamp': timestamp, 'value': handelerate, 'check_type': check_type, 'chart_type': 'Rate'})
        local_vars.append({'name': 'nginx_accept', 'timestamp': timestamp, 'value': acceptrate, 'check_type': check_type, 'chart_type': 'Rate'})
        local_vars.append({'name': 'nginx_reading', 'timestamp': timestamp, 'value': reading, 'check_type': check_type})
        local_vars.append({'name': 'nginx_writing', 'timestamp': timestamp, 'value': writing, 'check_type': check_type})
        local_vars.append({'name': 'nginx_waiting', 'timestamp': timestamp, 'value': waiting, 'check_type': check_type})

        return local_vars
    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass


