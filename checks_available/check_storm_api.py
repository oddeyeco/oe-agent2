import lib.record_rate
import lib.commonclient
import lib.getconfig
import lib.puylogger
import lib.basecheck
import json
import re

storm_host = lib.getconfig.getparam('Storm-API', 'host')
storm_port = lib.getconfig.getparam('Storm-API', 'port')
perspout = lib.getconfig.getparam('Storm-API', 'perspout')
perbolt = lib.getconfig.getparam('Storm-API', 'perbolt')

storm_url = 'http://' + storm_host + ':' + storm_port
check_type = 'storm'

scounters = ['emitted', 'transferred', 'acked', 'failed']

snoncounters = ['requestedMemOnHeap', 'requestedMemOffHeap', 'requestedCpu', 'completeLatency']
bnoncounters = ['requestedMemOnHeap', 'requestedMemOffHeap', 'requestedCpu', 'processLatency', 'executeLatency', 'capacity']

class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            topology_list = json.loads(lib.commonclient.httpget(__name__, storm_url+'/api/v1/topology/summary'))

            for x in topology_list['topologies']:
                topology_id = x['id']
                topology_name = x['name']
                tp = json.loads(lib.commonclient.httpget(__name__, storm_url+'/api/v1/topology/' + topology_id))
                for tpstats in tp['topologyStats']:
                    if tpstats['windowPretty'] == 'All time':
                        for l in scounters:
                            last_value = self.last.return_last_value('storm_base' + l, tpstats[l])
                            if tpstats[l] is None:
                                self.local_vars.append({'name': 'storm_' + l, 'timestamp': self.timestamp,
                                'value': 0, 'check_type': check_type + '_topology', 'chart_type': 'Counter',
                                'extra_tag': {'name': topology_name}})
                            elif tpstats[l] > last_value:
                                self.local_vars.append({'name': 'storm_' + l, 'timestamp': self.timestamp,
                                'value': tpstats[l], 'check_type': check_type + '_topology', 'chart_type': 'Counter',
                                'extra_tag': {'name': topology_name}})
                if perbolt is True:
                    for spout in tp['spouts']:
                        for l in scounters:
                            self.local_vars.append({'name': 'storm_' + l, 'timestamp': self.timestamp,
                            'value': spout[l], 'check_type': check_type + '_spout', 'chart_type': 'Counter',
                            'extra_tag': {'topology': topology_name, 'name': spout['spoutId']}})
                        for m in snoncounters:
                            z = re.sub('([A-Z]{1})', r'_\1', m).lower()
                            self.local_vars.append({'name': 'storm_' + z, 'timestamp': self.timestamp,
                            'value': spout[m], 'check_type': check_type + '_spout',
                            'extra_tag': {'topology': topology_name, 'name': spout['spoutId']}})

                    for bolt in tp['bolts']:
                        for l in scounters:
                            self.local_vars.append({'name': 'storm_' + l, 'timestamp': self.timestamp,
                            'value': bolt[l], 'check_type': check_type + '_bolt', 'chart_type': 'Counter',
                            'extra_tag': {'topology': topology_name, 'name': bolt['boltId']}})
                        self.local_vars.append({'name': 'storm_executed', 'timestamp': self.timestamp,
                        'value': bolt['executed'], 'check_type': check_type + '_bolt', 'chart_type': 'Counter',
                        'extra_tag': {'topology': topology_name, 'name': bolt['boltId']}})
                        for m in bnoncounters:
                            z = re.sub('([A-Z]{1})', r'_\1', m).lower()
                            self.local_vars.append({'name': 'storm_' + z, 'timestamp': self.timestamp,
                            'value': bolt[m], 'check_type': check_type + '_bolt',
                            'extra_tag': {'topology': topology_name, 'name': bolt['boltId']}})

        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass


