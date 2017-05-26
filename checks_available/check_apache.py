import lib.getconfig
import datetime
import lib.pushdata
import lib.record_rate
import lib.puylogger
import lib.commonclient


apache_url = lib.getconfig.getparam('Apache', 'url')

apache_auth = lib.getconfig.getparam('Apache', 'user')+':'+lib.getconfig.getparam('Apache', 'pass')
curl_auth = lib.getconfig.getparam('Apache', 'auth')
cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')


def runcheck():
    try:
        if curl_auth is True:
            lib.commonclient.httpget(__name__, apache_url, apache_auth)
        else:
            lib.commonclient.httpget(__name__, apache_url)

        jsondata = lib.pushdata.JonSon()
        jsondata.prepare_data()
        rate = lib.record_rate.ValueRate()
        check_type = 'apache'
        metrics_rated = ('Total Accesses', 'Total kBytes')
        metrics_stuck = ('ReqPerSec', 'BytesPerSec', 'BytesPerReq', 'BusyWorkers', 'IdleWorkers')
        timestamp = int(datetime.datetime.now().strftime("%s"))
        for line in t.contents.split('\n'):
            for searchitem in  metrics_stuck:
                if searchitem in line:
                    key = line.split(' ')[0].replace(':', '')
                    value = line.split(' ')[1]
                    jsondata.gen_data('apache_'+key, timestamp, value, lib.pushdata.hostname, check_type, cluster_name)
            for searchitem in  metrics_rated:
                reaction = 0
                metr_type = 'Rate'
                if searchitem in line:
                    key = line.split(' ')[0]+line.split(' ')[1].replace(':', '')
                    value = line.split(' ')[2]
                    value_rate = rate.record_value_rate(key, value, timestamp)
                    jsondata.gen_data('apache_'+key, timestamp, value_rate, lib.pushdata.hostname, check_type, cluster_name, reaction, metr_type)

        jsondata.put_json()
    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass


