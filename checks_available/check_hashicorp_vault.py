import lib.record_rate
import lib.commonclient
import lib.getconfig
import lib.puylogger
import lib.basecheck
import json

url = lib.getconfig.getparam('Hashicorp-Vault', 'telemetery')
token = 'X-Vault-Token: ' + lib.getconfig.getparam('Hashicorp-Vault', 'token')
detailed = lib.getconfig.getparam('Hashicorp-Vault', 'detailed')
getrated = lib.getconfig.getparam('Hashicorp-Vault', 'getrates')

check_type = 'vault'

class Check(lib.basecheck.CheckBase):
    def precheck(self):
        try:
            stats_json = json.loads(lib.commonclient.httpget(__name__, url, headers=token))
            for index in range(0, len(stats_json['Gauges'])):
                self.local_vars.append({'name': stats_json['Gauges'][index]['Name'].replace('.', '_').replace('-', '_').lower(), 'timestamp': self.timestamp, 'value': float(stats_json['Gauges'][index]['Value']), 'check_type': check_type})

            if detailed:
                if getrated:
                    for index in range(0, len(stats_json['Samples'])):
                        self.local_vars.append({'name': stats_json['Samples'][index]['Name'].replace('.', '_').replace('-', '_').lower(), 'timestamp': self.timestamp, 'value': float(stats_json['Samples'][index]['Rate']), 'check_type': check_type})
                else:
                    for index in range(0, len(stats_json['Samples'])):
                        self.local_vars.append({'name': stats_json['Samples'][index]['Name'].replace('.', '_').replace('-', '_').lower(), 'timestamp': self.timestamp, 'value': float(stats_json['Samples'][index]['Count']), 'check_type': check_type})

        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass



