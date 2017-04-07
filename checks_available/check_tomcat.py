'''

In order to use this check jxmadmin role and user should be enabled.
Edit $CATALINA_HOME/conf/tomcat-users.xml and add following inside tomcat-users section :

<role rolename="manager-jmx"/>
<user username="foo" password="foo" roles="manager-jmx"/>

'''

import lib.record_rate, lib.pushdata
import urllib2
import os, sys, re
import ConfigParser
import datetime

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/webservers.ini')

tomcat_url = config.get('Tomcat', 'url')
tomcat_user = config.get('Tomcat', 'user')
tomcat_pass = config.get('Tomcat', 'pass')
cluster_name = config.get('SelfConfig', 'cluster_name')
check_type = 'tomcat'

def runcheck():
    try:
        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()

        urls=[tomcat_url+'?qry=java.lang:type=Memory', tomcat_url+'?qry=java.lang:type=Threading', tomcat_url+'?qry=java.lang:type=GarbageCollector,name=*']

        password_mgr.add_password(None, urls, tomcat_user, tomcat_pass)
        handler = urllib2.HTTPBasicAuthHandler(password_mgr)
        opener = urllib2.build_opener(handler)

        tmemstats=opener.open(urls[0],timeout=5).read().splitlines()
        threadstats = opener.open(urls[1], timeout=5).read().splitlines()
        gcstats = opener.open(urls[2], timeout=5).read()#.splitlines()

        urllib2.install_opener(opener)
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

        gcdurations=re.findall('duration='+"[+-]?\d+(?:\.\d+)?" , gcstats)
        for index, s in enumerate(gcdurations):
            jsondata.gen_data('tomcat_lastgc_' + str(index) , timestamp, s.split('=')[1], lib.pushdata.hostname, check_type, cluster_name)

        jsondata.put_json()
    except Exception as e:
        lib.pushdata.print_error(__name__ , (e))
        pass

