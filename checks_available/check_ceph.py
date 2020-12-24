import subprocess
import json
import lib.getconfig
import lib.basecheck
import lib.puylogger

ceph_client = lib.getconfig.getparam('Ceph', 'client')
ceph_keyring = lib.getconfig.getparam('Ceph', 'keyring')
check_type = 'ceph'


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            command1 = 'ceph -n ' + ceph_client + ' --keyring=' + ceph_keyring + ' -s -f json'
            command2 = 'ceph -n ' + ceph_client + ' --keyring=' + ceph_keyring + ' pg stat -f json'
            command3 = 'ceph -n ' + ceph_client + ' --keyring=' + ceph_keyring + ' osd df -f json'

            p1 = subprocess.Popen(command1, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
            output1, err = p1.communicate()

            s1 = json.loads(output1)
            stats=s1['pgmap']
            health = s1['health']

            p2 = subprocess.Popen(command2, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
            output2, err = p2.communicate()
            pgstats = json.loads(output2)

            p3 = subprocess.Popen(command3, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
            output3, err = p3.communicate()
            osdstats = json.loads(output3)['nodes']

            if 'status' in health.keys():
                hs = health['status']
            else:
                hs = health['overall_status']

            if hs == 'HEALTH_OK':
                health_value = 0
                err_type = 'OK'
            elif hs == 'HEALTH_WARN':
                health_value = 9
                err_type = 'WARNING'
            else:
                health_value = 16
                err_type = 'ERROR'

            self.jsondata.send_special("Ceph-Health", self.timestamp, health_value, hs, err_type)
            try:
                s=str(health['checks']['PG_DEGRADED']['summary'])
                ceph_degraded_percent=s[s.find("(")+1:s.find(")")].replace('%', '')
            except:
                ceph_degraded_percent='0.0'

            try:
                u=str(health['checks']['OBJECT_MISPLACED']['summary'])
                ceph_misplaced_percent=u[u.find("(")+1:u.find(")")].replace('%', '')
            except:
                ceph_misplaced_percent='0.0'

            self.local_vars.append({'name': 'ceph_misplaced_percent', 'timestamp': self.timestamp, 'value': ceph_misplaced_percent, 'check_type': check_type})
            self.local_vars.append({'name': 'ceph_degraded_percent', 'timestamp': self.timestamp, 'value':ceph_degraded_percent, 'check_type': check_type})
            self.local_vars.append({'name': 'ceph_bytes_avail', 'timestamp': self.timestamp, 'value': stats['bytes_avail'], 'check_type': check_type})
            self.local_vars.append({'name': 'ceph_bytes_total', 'timestamp': self.timestamp, 'value': stats['bytes_total'], 'check_type': check_type})
            self.local_vars.append({'name': 'ceph_bytes_used', 'timestamp': self.timestamp, 'value': stats['bytes_used'], 'check_type': check_type})
            self.local_vars.append({'name': 'ceph_data_bytes', 'timestamp': self.timestamp, 'value': stats['data_bytes'], 'check_type': check_type})
            self.local_vars.append({'name': 'ceph_num_pgs', 'timestamp': self.timestamp, 'value': stats['num_pgs'], 'check_type': check_type})

            if 'io_sec' in pgstats:
                self.local_vars.append({'name': 'ceph_io_sec', 'timestamp': self.timestamp, 'value': pgstats['io_sec'], 'check_type': check_type, 'chart_type': 'Rate'})
            else:
                self.local_vars.append({'name': 'ceph_io_sec', 'timestamp': self.timestamp, 'value': 0, 'check_type': check_type, 'chart_type': 'Rate'})

            if 'read_bytes_sec' in stats:
                self.local_vars.append({'name': 'ceph_read_bytes_sec', 'timestamp': self.timestamp, 'value': stats['read_bytes_sec'], 'check_type': check_type, 'chart_type': 'Rate'})
            else:
                self.local_vars.append({'name': 'ceph_read_bytes_sec', 'timestamp': self.timestamp, 'value': 0, 'check_type': check_type, 'chart_type': 'Rate'})
            if 'write_bytes_sec' in stats:
                self.local_vars.append({'name': 'ceph_write_bytes_sec', 'timestamp': self.timestamp, 'value': stats['write_bytes_sec'], 'check_type': check_type, 'chart_type': 'Rate'})
            else:
                self.local_vars.append({'name': 'ceph_write_bytes_sec', 'timestamp': self.timestamp, 'value': 0, 'check_type': check_type, 'chart_type': 'Rate'})
            if 'degraded_objects' in stats:
                self.local_vars.append({'name': 'ceph_degraded_objects', 'timestamp': self.timestamp, 'value': stats['degraded_objects'], 'check_type': check_type})
            else:
                self.local_vars.append({'name': 'ceph_degraded_objects', 'timestamp': self.timestamp, 'value': 0, 'check_type': check_type})
            if 'degraded_ratio' in stats:
                self.local_vars.append({'name': 'ceph_degraded_ratio', 'timestamp': self.timestamp, 'value': stats['degraded_ratio'], 'check_type': check_type})
            else:
                self.local_vars.append({'name': 'ceph_degraded_ratio', 'timestamp': self.timestamp, 'value': 0.0, 'check_type': check_type})
            if 'degraded_total' in stats:
                self.local_vars.append({'name': 'ceph_degraded_total', 'timestamp': self.timestamp, 'value': stats['degraded_total'], 'check_type': check_type})
            else:
                self.local_vars.append({'name': 'ceph_degraded_total', 'timestamp': self.timestamp, 'value': 0, 'check_type': check_type})
            if 'misplaced_objects' in stats:
                self.local_vars.append({'name': 'ceph_misplaced_objects', 'timestamp': self.timestamp, 'value': stats['misplaced_objects'], 'check_type': check_type})
            else:
                self.local_vars.append({'name': 'ceph_misplaced_objects', 'timestamp': self.timestamp, 'value': 0, 'check_type': check_type})
            if 'misplaced_ratio' in stats:
                self.local_vars.append({'name': 'ceph_misplaced_ratio', 'timestamp': self.timestamp, 'value': stats['misplaced_ratio'], 'check_type': check_type})
            else:
                self.local_vars.append({'name': 'ceph_misplaced_ratio', 'timestamp': self.timestamp, 'value': 0.0, 'check_type': check_type})
            if 'misplaced_total' in stats:
                self.local_vars.append({'name': 'ceph_misplaced_total', 'timestamp': self.timestamp, 'value': stats['misplaced_total'], 'check_type': check_type})
            else:
                self.local_vars.append({'name': 'ceph_misplaced_total', 'timestamp': self.timestamp, 'value': 0, 'check_type': check_type})
            if 'recovering_bytes_per_sec' in stats:
                self.local_vars.append({'name': 'ceph_recovering_bytes_per_sec', 'timestamp': self.timestamp, 'value': stats['recovering_bytes_per_sec'], 'check_type': check_type})
            else:
                self.local_vars.append({'name': 'ceph_recovering_bytes_per_sec', 'timestamp': self.timestamp, 'value': 0, 'check_type': check_type})
            if 'num_objects_recovered' in stats:
                self.local_vars.append({'name': 'ceph_num_objects_recovered', 'timestamp': self.timestamp, 'value': stats['num_objects_recovered'], 'check_type': check_type})
            else:
                self.local_vars.append({'name': 'ceph_num_objects_recovered', 'timestamp': self.timestamp, 'value': 0, 'check_type': check_type})
            if 'recovering_keys_per_sec' in stats:
                self.local_vars.append({'name': 'ceph_recovering_keys_per_sec', 'timestamp': self.timestamp, 'value': stats['recovering_keys_per_sec'], 'check_type': check_type})
            else:
                self.local_vars.append({'name': 'ceph_recovering_keys_per_sec', 'timestamp': self.timestamp, 'value': 0, 'check_type': check_type})

            for lenq in range(0, len(osdstats)):
                space = {'utilization' : osdstats[lenq]['utilization'], 'space_avail' : osdstats[lenq]['kb_avail'], 'space_used': osdstats[lenq]['kb_used']}
                for k,v in space.items():
                    self.local_vars.append({'name': 'ceph_osd_' + str(k), 'timestamp': self.timestamp, 'value': v, 'check_type': check_type, 'extra_tag': {'osd_name': osdstats[lenq]['name']}})

        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass
