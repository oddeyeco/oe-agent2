import lib.record_rate
import lib.commonclient
import lib.getconfig
import lib.puylogger
import datetime

phpfpm_url = lib.getconfig.getparam('PhpFPM', 'address') + lib.getconfig.getparam('PhpFPM', 'stats')
phpfpm_auth = lib.getconfig.getparam('PhpFPM', 'user')+':'+lib.getconfig.getparam('PhpFPM', 'pass')
curl_auth = lib.getconfig.getparam('PhpFPM', 'auth')
cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_type = 'php-fpm'


def runcheck():
    try:
        local_vars = []
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
        timestamp = int(datetime.datetime.now().strftime("%s"))
        conns_per_sec = rate.record_value_rate('phpfpm_connections', connections, timestamp)

        local_vars.append({'name': 'phpfpm_conns_per_sec', 'timestamp': timestamp, 'value': conns_per_sec, 'check_type': check_type, 'chart_type': 'Rate'})
        local_vars.append({'name': 'phpfpm_proc_idle', 'timestamp': timestamp, 'value': proc_idle, 'check_type': check_type})
        local_vars.append({'name': 'phpfpm_proc_active', 'timestamp': timestamp, 'value': proc_active, 'check_type': check_type})
        local_vars.append({'name': 'phpfpm_proc_total', 'timestamp': timestamp, 'value': proc_total, 'check_type': check_type})
        local_vars.append({'name': 'phpfpm_max_active', 'timestamp': timestamp, 'value': max_active, 'check_type': check_type})
        local_vars.append({'name': 'phpfpm_max_children', 'timestamp': timestamp, 'value': max_children, 'check_type': check_type})
        local_vars.append({'name': 'phpfpm_slow_request', 'timestamp': timestamp, 'value': slow_request, 'check_type': check_type})


        return local_vars
    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass


