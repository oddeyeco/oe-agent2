'''
This check requires Python MySQLDB or pymysql, On Debian like systems do
APT: apt-get install python-mysqldb, or apt-get install python-pymysql
PIP: pip install MySQL-python or pip install pymysql
'''

import lib.basecheck
import lib.getconfig
import lib.puylogger
import lib.record_rate
import ast


try:
    import MySQLdb
    mysqldriver = MySQLdb
    lib.puylogger.print_message(__name__ + ' Using MySQLdb to connect to MySQL server')
except:
    try:
        import pymysql
        mysqldriver = pymysql
        lib.puylogger.print_message(__name__ + ' Using pymysql to connect to MySQL server')
    except:
        lib.puylogger.print_message(__name__ + ' Error : Cannot load MySQL module, please install MySQLdb or pymysql ')

mysql_host = lib.getconfig.getparam('MySQL', 'host')
mysql_user = lib.getconfig.getparam('MySQL', 'user')
mysql_pass = lib.getconfig.getparam('MySQL', 'pass')

advanced = lib.getconfig.getparam('MySQL', 'advanced')
check_type = 'mysql'

if advanced:
    custom_querry = ast.literal_eval(lib.getconfig.getparam('MySQL', 'custom_query'))


class Check(lib.basecheck.CheckBase):

    def precheck(self):
        try:
            db = mysqldriver.connect(host=mysql_host, user=mysql_user, passwd=mysql_pass, )
            cur = db.cursor()
            raw_mysqlstats = cur.execute("SHOW GLOBAL STATUS WHERE Variable_name='Connections'"
                                "OR Variable_name='Com_select' "
                                "OR Variable_name='Com_delete_multi' "
                                "OR Variable_name='Com_delete' "
                                "OR Variable_name='Com_insert' "
                                "OR Variable_name='Com_update' "
                                "OR Variable_name LIKE 'Bytes_%' "
                                "OR Variable_name='Queries' "
                                "OR Variable_name='Questions' "        
                                "OR Variable_name='Slow_queries' "
                                "OR Variable_name='Qcache_hits' "
                                "OR Variable_name='Open_files' "
                                "OR Variable_name='Max_used_connections' "
                                "OR Variable_name='Threads_connected' "
                                "OR Variable_name='Innodb_rows_deleted' "
                                "OR Variable_name='Innodb_rows_inserted' "
                                "OR Variable_name='Innodb_rows_read' "        
                                "OR Variable_name='Innodb_rows_updated' "
                                "OR Variable_name='Innodb_data_read' "
                                "OR Variable_name='Innodb_data_writes' "
                                "OR Variable_name='Innodb_buffer_pool_read_requests' "
                                "OR Variable_name='Innodb_buffer_pool_write_requests' "
                                "OR Variable_name='Innodb_data_fsyncs' "
                                "")
            non_rate_metrics = ('Max_used_connections', 'Slow_queries', 'Open_files', 'Threads_connected')
            for row in cur.fetchall():
                mytype = row[0]
                myvalue = row[1]
                if mytype in non_rate_metrics:
                    self.local_vars.append({'name': 'mysql_'+ mytype.lower(), 'timestamp': self.timestamp, 'value': myvalue, 'check_type': check_type, })
                else:
                    vrate = self.rate.record_value_rate('mysql_' + mytype, myvalue, self.timestamp)
                    self.local_vars.append({'name': 'mysql_' + mytype.lower(), 'timestamp': self.timestamp, 'value': vrate, 'check_type': check_type, 'chart_type': 'Rate'})

            if advanced:
                for i in custom_querry:
                    cr = db.cursor()
                    cr.execute(custom_querry[i])
                    for row in cr.fetchall():
                        value = float(row[0])
                        self.local_vars.append({'name': 'mysql_custom_querry', 'timestamp': self.timestamp, 'value': value, 'check_type': check_type, 'extra_tag': {'prettyname': i}})
            cur.close()
            db.close()
        except Exception as e:
            lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
            pass

