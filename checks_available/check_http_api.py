import lib.record_rate
import lib.puylogger
import lib.pushdata
import lib.getconfig
import lib.commonclient
import time
import lib.basecheck
import re

http_auth = lib.getconfig.getparam('HTTP', 'user')+':'+lib.getconfig.getparam('HTTP', 'pass')
curl_auth = lib.getconfig.getparam('HTTP', 'auth')
http_upstream = lib.getconfig.getparam('HTTP', 'upstream').split(',')

check_type = 'http_api'

p = '(?:http.*://)?(?P<host>[^:/ ]+).?(?P<port>[0-9]*).*'


class Check(lib.basecheck.CheckBase):

    def precheck(self):
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

                extag = m.group('host').replace('.', '_') + '_' + port
                start_time = time.time()
                if curl_auth is True:
                    t = lib.commonclient.httpget(__name__, app, http_auth)
                else:
                    t = lib.commonclient.httpget(__name__, app)

                resptime = ((time.time() - start_time))
                self.local_vars.append({'name': 'http_api', 'timestamp': self.timestamp, 'value': resptime, 'check_type': check_type, 'extra_tag': {'apihost': extag}})
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
