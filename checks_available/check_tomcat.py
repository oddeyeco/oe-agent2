'''

In order to use this check jxmadmin role and user should be enabled.
Edit $CATALINA_HOME/conf/tomcat-users.xml and add following inside tomcat-users section :

<role rolename="manager-jmx"/>
<user username="foo" password="foo" roles="manager-jmx"/>

'''

#import lib.record_rate
import lib.pushdata
import lib.getconfig
import lib.commonclient
import lib.puylogger
import re
import datetime

tomcat_url = lib.getconfig.getparam('Tomcat', 'url')
tomcat_user = lib.getconfig.getparam('Tomcat', 'user')
tomcat_pass = lib.getconfig.getparam('Tomcat', 'pass')
tomcat_auth = lib.getconfig.getparam('Tomcat', 'user')+':'+lib.getconfig.getparam('Tomcat', 'pass')
cluster_name = lib.getconfig.getparam('SelfConfig', 'cluster_name')
check_type = 'tomcat'

def runcheck():
    try:
        urls=[tomcat_url+'?qry=java.lang:type=Memory', tomcat_url+'?qry=java.lang:type=Threading', tomcat_url+'?qry=java.lang:type=GarbageCollector,name=*']

        tmemstats = lib.commonclient.httpget(__name__, urls[0], tomcat_auth).splitlines()
        threadstats = lib.commonclient.httpget(__name__, urls[1], tomcat_auth).splitlines()
        gcstats = str(lib.commonclient.httpget(__name__, urls[2], tomcat_auth).splitlines())
        jsondata=lib.pushdata.JonSon()
        jsondata.prepare_data()
        timestamp = int(datetime.datetime.now().strftime("%s"))
        memstats = ('HeapMemoryUsage', 'NonHeapMemoryUsage')
        threads = ('PeakThreadCount', 'DaemonThreadCount', 'ThreadCount', 'TotalStartedThreadCount')

        for line in tmemstats:
            for serchitem in memstats:
                if line.startswith(serchitem):
                    metrics=line.split("contents=", 1)[1].replace(')', '').replace('=', ' ').replace('}', '').replace('{', '').replace(',', '').split()
                    jsondata.gen_data('tomcat_' + serchitem.replace('MemoryUsage', '').lower() + '_commited', timestamp, metrics[1], lib.pushdata.hostname, check_type, cluster_name)
                    jsondata.gen_data('tomcat_' + serchitem.replace('MemoryUsage', '').lower() + '_init', timestamp, metrics[3], lib.pushdata.hostname, check_type, cluster_name)
                    jsondata.gen_data('tomcat_' + serchitem.replace('MemoryUsage', '').lower() + '_used', timestamp, metrics[5], lib.pushdata.hostname, check_type, cluster_name)
                    jsondata.gen_data('tomcat_' + serchitem.replace('MemoryUsage', '').lower() + '_max', timestamp, metrics[7], lib.pushdata.hostname, check_type, cluster_name)

        for line in threadstats:
            for serchitem in threads:
                if line.startswith(serchitem):
                    sender=line.replace(':', '').split()
                    jsondata.gen_data('tomcat_' + sender[0].lower(), timestamp, sender[1], lib.pushdata.hostname, check_type, cluster_name)

        gcdurations = re.findall('duration='+"[+-]?\d+(?:\.\d+)?" , gcstats)
        for index, s in enumerate(gcdurations):
            jsondata.gen_data('tomcat_lastgc_' + str(index) , timestamp, s.split('=')[1], lib.pushdata.hostname, check_type, cluster_name)

        jsondata.put_json()

    except Exception as e:
        lib.puylogger.print_message(__name__ + ' Error : ' + str(e))
        pass

