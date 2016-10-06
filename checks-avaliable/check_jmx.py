# Requires jpype, Please install it (apt-get install python-jpype)
import os, sys
import ConfigParser
import datetime
import socket

import jpype
from jpype import java
from jpype import javax

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')

HOST= config.get('JMX', 'host')
PORT= config.get('JMX', 'port')
USER= config.get('JMX', 'user')
PASS= config.get('JMX', 'pass')
TYPE= config.get('JMX', 'gctype')
JAVA= config.get('JMX', 'java_home')
URL = 'service:jmx:rmi:///jndi/rmi://'+HOST+':'+PORT+'/jmxrmi'

hostname = socket.getfqdn()
cluster_name = config.get('SelfConfig', 'cluster_name')
check_type = 'jmx'

if TYPE == 'G1':
    CMS=False
    G1=True
if TYPE == 'CMS':
    CMS=True
    G1=False

os.environ['JAVA_HOME'] = JAVA

def run_jmx():
    JAVA = config.get('JMX', 'java_home')

    #jpype.startJVM(jpype.getDefaultJVMPath())

    def init_jvm(jvmpath=None):
        if jpype.isJVMStarted():
            return
        jpype.startJVM(jpype.getDefaultJVMPath())

    init_jvm()
    try:
        os.environ['JAVA_HOME'] = JAVA
        #print os.environ['JAVA_HOME']

        jhash = java.util.HashMap()
        jarray = jpype.JArray(java.lang.String)([USER, PASS])
        jhash.put(javax.management.remote.JMXConnector.CREDENTIALS, jarray);
        jmxurl = javax.management.remote.JMXServiceURL(URL)
        jmxsoc = javax.management.remote.JMXConnectorFactory.connect(jmxurl, jhash)
        connection = jmxsoc.getMBeanServerConnection();

        object = 'java.lang:type=Memory'
        attribute = 'HeapMemoryUsage'
        attr = connection.getAttribute(javax.management.ObjectName(object), attribute)
        HeapUsed = attr.contents.get('used')
        HeapCommited = attr.contents.get('committed')
        HeapInit =  attr.contents.get('init')
        HeapMax =  attr.contents.get('max')

        sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
        push = __import__('pushdata')
        value_rate= __import__('record_rate')
        rate=value_rate.ValueRate()
        jsondata=push.JonSon()
        jsondata.create_data()
        timestamp = int(datetime.datetime.now().strftime("%s"))

        jsondata.gen_data('jmx_' + 'HeapUsed', timestamp, HeapUsed, push.hostname, check_type, cluster_name)
        jsondata.gen_data('jmx_' + 'HeapCommited', timestamp, HeapCommited, push.hostname, check_type, cluster_name)
        jsondata.gen_data('jmx_' + 'HeapInit', timestamp, HeapInit, push.hostname, check_type, cluster_name)
        jsondata.gen_data('jmx_' + 'HeapMax', timestamp, HeapMax, push.hostname, check_type, cluster_name)

        #print 'HeapUsed', HeapUsed
        #print 'HeapCommited', HeapCommited
        #print 'HeapInit', HeapInit
        #print 'HeapMax', HeapMax

        if CMS is True:
            object = 'java.lang:type=GarbageCollector,name=ConcurrentMarkSweep'
            GcCount = 'CollectionCount'
            ColCount = connection.getAttribute(javax.management.ObjectName(object), GcCount)

            GcTime = 'CollectionTime'
            ColTime = connection.getAttribute(javax.management.ObjectName(object), GcTime)
            jsondata.gen_data('jmx_' + 'CMSGcCount', timestamp, ColCount, push.hostname, check_type, cluster_name)
            GcTime_rate = rate.record_value_rate('jmx_CMSGcTime', ColTime.value, timestamp)
            jsondata.gen_data('jmx_CMSGcTime', timestamp, GcTime_rate, push.hostname, check_type, cluster_name)

            object = 'java.lang:type=GarbageCollector,name=ParNew'
            PnGcCount = 'CollectionCount'
            PnColCount = connection.getAttribute(javax.management.ObjectName(object), PnGcCount)

            PnGcTime = 'CollectionTime'
            PnColTime = connection.getAttribute(javax.management.ObjectName(object), PnGcTime)
            jsondata.gen_data('jmx_' + 'ParNewGcCount', timestamp, PnColCount, push.hostname, check_type, cluster_name)
            GcTime_rate = rate.record_value_rate('jmx_ParNewGcTime', PnColTime.value, timestamp)
            jsondata.gen_data('jmx_ParNewGcTime', timestamp, GcTime_rate, push.hostname, check_type, cluster_name)


            #print  'CMSGcCount', ColCount
            #print  'CMSGcTime', ColTime

        if G1 is True:
            object = 'java.lang:type=GarbageCollector,name=G1 Old Generation'
            OldGcCount = 'CollectionCount'
            OldColCount = connection.getAttribute(javax.management.ObjectName(object), OldGcCount)

            OldGcTime = 'CollectionTime'
            OldColTime = connection.getAttribute(javax.management.ObjectName(object), OldGcTime)

            jsondata.gen_data('jmx_' + 'OldGcCount', timestamp, OldColCount, push.hostname, check_type, cluster_name)
            OldGcTime_rate = rate.record_value_rate('jmx_OldGcTime', OldColTime.value, timestamp)
            jsondata.gen_data('jmx_OldGcTime', timestamp, OldGcTime_rate, push.hostname, check_type, cluster_name)

            object = 'java.lang:type=GarbageCollector,name=G1 Young Generation'
            YoungGcCount = 'CollectionCount'
            YoungColCount = connection.getAttribute(javax.management.ObjectName(object), YoungGcCount)

            YoungGcTime = 'CollectionTime'
            YoungColTime = connection.getAttribute(javax.management.ObjectName(object), YoungGcTime)

            jsondata.gen_data('jmx_' + 'YoungGcCount', timestamp, YoungColCount, push.hostname, check_type, cluster_name)
            YoungColTime_rate = rate.record_value_rate('jmx_YoungColTime', YoungColTime.value, timestamp)
            jsondata.gen_data('jmx_YoungGcTime', timestamp, YoungColTime_rate, push.hostname, check_type, cluster_name)

            #print YoungColTime.value
            #print  'YoungGcCount', YoungColCount
            #print  'YoungGcTime', YoungColTime
            #print  'OldGcCount', OldColCount
            #print  'OldGcTime', OldColTime

        jsondata.put_json()
        jsondata.truncate_data()

    except Exception as e:
        push = __import__('pushdata')
        push.print_error(__name__ , (e))
        pass
