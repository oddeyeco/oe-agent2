import subprocess
import json
import lib.getconfig
import lib.basecheck
import lib.puylogger
import lib.record_rate


varnish_client = lib.getconfig.getparam('Varnish', 'varnishstat')
varnish_user = lib.getconfig.getparam('Varnish', 'varnishuser')
check_type = 'varnish'


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            command1 = 'sudo -u ' + varnish_user + ' ' + varnish_client + ' -j'
            p1 = subprocess.Popen(command1, stdout=subprocess.PIPE, shell=True, universal_newlines=True)
            output1, err = p1.communicate()
            s1 = json.loads(output1)
            ratedstats = ('MAIN.sess_conn', 'MAIN.client_req', 'MAIN.cache_hit', 'MAIN.cache_miss', 'MAIN.cache_hitpass')
            stats = ('MAIN.threads' , 'MAIN.threads_created', 'MAIN.threads_failed', 'MAIN.threads_limited', 'MAIN.thread_queue_len', 'MAIN.sess_queued',
                     'MAIN.backend_conn', 'MAIN.backend_recycle', 'MAIN.backend_reuse', 'MAIN.backend_toolate', 'MAIN.backend_fail', 'MAIN.backend_unhealthy',
                     'MAIN.backend_busy', 'MAIN.backend_req', 'MAIN.n_expired', 'MAIN.n_lru_nuked', 'MAIN.sess_dropped'
                    )
            for rstat in ratedstats:
                rte = self.rate.record_value_rate('varnish_' + rstat, s1[rstat]['value'], self.timestamp)
                self.local_vars.append({'name': 'varnish_' + rstat.replace('MAIN.', ''), 'timestamp': self.timestamp, 'value': rte, 'check_type': check_type})

            for stat in stats:
                if stat in s1:
                    self.local_vars.append({'name': 'varnish_' + stat.replace('MAIN.', ''), 'timestamp': self.timestamp, 'value': s1[stat]['value'], 'check_type': check_type})

        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass

