import lib.record_rate
import lib.pushdata
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
        jsondata = lib.pushdata.JonSon()
        jsondata.prepare_data()
        rate = lib.record_rate.ValueRate()
        timestamp = int(datetime.datetime.now().strftime("%s"))
        conns_per_sec = rate.record_value_rate('phpfpm_connections', connections, timestamp)
        jsondata.gen_data('phpfpm_conns_per_sec', timestamp, conns_per_sec, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')
        jsondata.gen_data('phpfpm_proc_idle', timestamp, proc_idle, lib.pushdata.hostname, check_type, cluster_name)
        jsondata.gen_data('phpfpm_proc_active', timestamp, proc_active, lib.pushdata.hostname, check_type, cluster_name)
        jsondata.gen_data('phpfpm_proc_total', timestamp, proc_total, lib.pushdata.hostname, check_type, cluster_name)
        jsondata.gen_data('phpfpm_max_active', timestamp, max_active, lib.pushdata.hostname, check_type, cluster_name)
        jsondata.gen_data('phpfpm_max_children', timestamp, max_children, lib.pushdata.hostname, check_type, cluster_name)
        jsondata.gen_data('phpfpm_slow_request', timestamp, slow_request, lib.pushdata.hostname, check_type, cluster_name)
        jsondata.put_json()
    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass


