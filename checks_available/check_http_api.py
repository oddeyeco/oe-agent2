import lib.record_rate
import lib.puylogger
import lib.pushdata
import lib.getconfig
import lib.commonclient
import time
import datetime
import re

http_auth = lib.getconfig.getparam('HTTP', 'user')+':'+lib.getconfig.getparam('HTTP', 'pass')
curl_auth = lib.getconfig.getparam('HTTP', 'auth')
cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
http_upstream = lib.getconfig.getparam('HTTP', 'upstream').split(',')

check_type = 'http'

p = '(?:http.*://)?(?P<host>[^:/ ]+).?(?P<port>[0-9]*).*'


def runcheck():
    local_vars = []
    try:
        for application in http_upstream:
            app = application.replace(' ', '')
            m = re.search(p, app)

            if not m.group('port'):
                if 'https' in app:
                    port = '443'
                else:
                    port = '80'
            else:
                port = m.group('port')
            m.group('host')

            name = 'http_' + m.group('host').replace('.', '_') + '_' + port

            timestamp = int(datetime.datetime.now().strftime("%s"))
            start_time = time.time()

            if curl_auth is True:
                t = lib.commonclient.httpget(__name__, app, http_auth)
            else:
                t = lib.commonclient.httpget(__name__, app)

            resptime = ((time.time() - start_time))
            local_vars.append({'name': name, 'timestamp': timestamp, 'value': resptime, 'check_type': check_type})
        return local_vars
    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass
