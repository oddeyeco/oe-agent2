import subprocess
import json
import lib.getconfig
import lib.basecheck
import lib.puylogger
import lib.record_rate


fdb_client = lib.getconfig.getparam('FoundationDB', 'fdbclipath')
check_type = 'foundationdb'


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            command1 = fdb_client + ' --exec "status json"'
            p1 = subprocess.Popen(command1, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
            output1, err = p1.communicate()
            s1 = json.loads(output1)
            wkl = ('bytes', 'keys', 'operations', 'transactions')
            wkops = ('read', 'written', 'read_requests', 'reads', 'writes' 'committed' ,'conflicted', 'started')

            for l in wkl:
                for w in wkops:
                    if w in s1['cluster']['workload'][l]:
                        rte = self.rate.record_value_rate('fdb_'+ str(l) + '_' + str(w), s1['cluster']['workload'][l][w]['counter'], self.timestamp)
                        self.local_vars.append({'name': 'fdb_'+ str(l) + '_' + str(w), 'timestamp': self.timestamp, 'value': rte, 'check_type': check_type})

            mmemory = ('committed_bytes', 'free_bytes', 'total_bytes')

            for key in s1['cluster']['machines'].keys():
                address = str(s1['cluster']['machines'][key]['address'])
                for mm in mmemory:
                    self.local_vars.append({'name': 'fdb_memory_' + mm, 'timestamp': self.timestamp, 'value': s1['cluster']['machines'][key]['memory'][mm], 'check_type': check_type, 'extra_tag': {'node': address}})

            self.local_vars.append({'name': 'fdb_connected_clients', 'timestamp': self.timestamp, 'value': s1['cluster']['clients']['count'], 'check_type': check_type})

            for mp in s1['cluster']['data']['moving_data']:
                self.local_vars.append({'name': 'fdb_moving_data', 'timestamp': self.timestamp, 'value': s1['cluster']['data']['moving_data'][mp], 'check_type': check_type, 'extra_tag': {'fdb_move_type': mp}})

            self.local_vars.append({'name': 'fdb_total_disk_used_bytes', 'timestamp': self.timestamp, 'value': s1['cluster']['data']['total_disk_used_bytes'], 'check_type': check_type})
            self.local_vars.append({'name': 'fdb_total_kv_size_bytes', 'timestamp': self.timestamp, 'value': s1['cluster']['data']['total_kv_size_bytes'], 'check_type': check_type})

        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass

