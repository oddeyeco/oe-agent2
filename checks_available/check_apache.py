import lib.getconfig
import datetime
import lib.record_rate
import lib.puylogger
import lib.commonclient


apache_url = lib.getconfig.getparam('Apache', 'url')

apache_auth = lib.getconfig.getparam('Apache', 'user')+':'+lib.getconfig.getparam('Apache', 'pass')
curl_auth = lib.getconfig.getparam('Apache', 'auth')
cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_type = 'apache'

def runcheck():
    local_vars = []
    try:
        if curl_auth is True:
            data = lib.commonclient.httpget(__name__, apache_url, apache_auth)
        else:
            data = lib.commonclient.httpget(__name__, apache_url)

        rate = lib.record_rate.ValueRate()

        metrics_rated = ('Total Accesses', 'Total kBytes')
        metrics_stuck = ('ReqPerSec', 'BytesPerSec', 'BytesPerReq', 'BusyWorkers', 'IdleWorkers')
        timestamp = int(datetime.datetime.now().strftime("%s"))
        for line in data.split('\n'):
            for searchitem in  metrics_stuck:
                if searchitem in line:
                    key = line.split(' ')[0].replace(':', '')
                    value = line.split(' ')[1]
                    local_vars.append({'name': 'apache_'+key.lower(), 'timestamp': timestamp, 'value': value, 'check_type': check_type})
            for searchitem in  metrics_rated:
                reaction = 0
                if searchitem in line:
                    key = line.split(' ')[0]+line.split(' ')[1].replace(':', '')
                    value = line.split(' ')[2]
                    value_rate = rate.record_value_rate(key, value, timestamp)
                    local_vars.append({'name': 'apache_' + key.lower(), 'timestamp': timestamp, 'value': value_rate, 'check_type': check_type, 'chart_type': 'Rate'})

        return local_vars
    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass


