'''
This check required Python MySQLDB, On Debian like systems do
apt-get install python-mysqldb
or
pip install MySQL-python
'''


import MySQLdb
import datetime
import ConfigParser
import os, sys
from lib.pushdata import JonSon,hostname,print_error
from lib.record_rate import ValueRate

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/sql_cache.ini')
cluster_name = config.get('SelfConfig', 'cluster_name')

mysql_host = config.get('MySQL', 'host')
mysql_user = config.get('MySQL', 'user')
mysql_pass = config.get('MySQL', 'pass')

def run_mysql():
    try:
        check_type = 'mysql'
        db = MySQLdb.connect(host=mysql_host, user=mysql_user, passwd=mysql_pass, )
        cur = db.cursor()
        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        jsondata=JonSon()
        jsondata.prepare_data()
        rate=ValueRate()
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
        timestamp = int(datetime.datetime.now().strftime("%s"))
        non_rate_metrics=('Max_used_connections', 'Slow_queries', 'Open_files', 'Threads_connected')
        for row in cur.fetchall():
            mytype = row[0].lower()
            myvalue = row[1]
            if mytype not in non_rate_metrics:
                myvalue=rate.record_value_rate('mysql_'+mytype, myvalue, timestamp)
                jsondata.gen_data('mysql_' + mytype, timestamp, myvalue, hostname, check_type, cluster_name, 0, 'Rate')
            else:
                jsondata.gen_data('mysql_'+mytype, timestamp, myvalue, hostname, check_type, cluster_name)
        jsondata.put_json()
    except Exception as e:
        print_error(__name__ , (e))
        pass


