import lib.record_rate
import lib.pushdata
import lib.commonclient
import lib.getconfig
import lib.puylogger
import datetime

nginx_url = lib.getconfig.getparam('NginX', 'address') + lib.getconfig.getparam('NginX', 'stats')
nginx_auth = lib.getconfig.getparam('NginX', 'user')+':'+lib.getconfig.getparam('NginX', 'pass')
curl_auth = lib.getconfig.getparam('NginX', 'auth')
cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')


def runcheck():
    try:

        if curl_auth is True:
            data = lib.commonclient.httpget(__name__, nginx_url, nginx_auth)
        else:
            data = lib.commonclient.httpget(__name__, nginx_url)

        jsondata=lib.pushdata.JonSon()
        jsondata.prepare_data()
        rate=lib.record_rate.ValueRate()
        check_type = 'nginx'

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

        jsondata.gen_data('nginx_connections', timestamp, connections, lib.pushdata.hostname, check_type, cluster_name)
        jsondata.gen_data('nginx_requests', timestamp, reqrate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')
        jsondata.gen_data('nginx_handled', timestamp, handelerate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')
        jsondata.gen_data('nginx_accept', timestamp, acceptrate, lib.pushdata.hostname, check_type, cluster_name, 0, 'Rate')
        jsondata.gen_data('nginx_reading', timestamp, reading, lib.pushdata.hostname, check_type, cluster_name)
        jsondata.gen_data('nginx_writing', timestamp, writing, lib.pushdata.hostname, check_type, cluster_name)
        jsondata.gen_data('nginx_waiting', timestamp, waiting, lib.pushdata.hostname, check_type, cluster_name)

        jsondata.put_json()
    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass


