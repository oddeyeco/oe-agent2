**PuyPuy**
---------

PuyPuy is python2 metrics collection daemon, which works with KairosDB, OpenTDB, Graphite and InfluxDB, For InfluxDB, KairosDB and OpenTSDB it uses REST interface, for Graphite Pickle.

Main idea behind PuyPuy is simplicity and less as possible dependencies, it is tested on Debian and Ubuntu systems, but should work on any Linux system.   

To install PuyPuy just clone our repository, make sure that you have few python dependency modules (pycurl, daemon) for base program.

If you use specific checks like check_mysql, MySQLdb should also be installed.
If you are going to use JMX check you will need module called python-jpype. 

Standard python-jpype which comes with Debian has dependency of default-jre, so apt-get install python-jpype will install lots of unwanted software, especially if you use Host-Spot JVM. 
To avoid that we have recreated python-jpype and removed default-jre dependency. You can download and use it. 

    wget http://apt.netangels.net/pool/main/p/python-jpype/python-jpype_0.5.4.2-3_amd64.deb
    dpkg -i python-jpype_0.5.4.2-3_amd64.deb

Tested on Debian 7 and 8, most likely will work for Ubuntu 

If you like python pip, then :
 
    pip install jpype 
    
Make your changes if needed in config.ini and run 

    ./puypuy.sh start
Python daemon process will start, run all python scripts from checks_avaliable directory as well as all check_* files scripts_available directory. 

**Create own python module :**

Create file in checks_enabled directory with namecheck_checkname.py, inside script you should have function with name run_checkname(Here you actual check should live). 
Your check should contain some  minimal imports in order to talk to main program: 

	hostname = socket.getfqdn()
	cluster_name = config.get('SelfConfig', 'cluster_name')
	check_type = 'test'

	def run_checkname()
	    sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
	    push = __import__('pushdata')
	    jsondata=push.JonSon()
	    jsondata.create_data()
	    timestamp = int(datetime.datetime.now().strftime("%s"))
		name='CheckName'
	    value=10

This will import needed libs to generate and send to time series server needed json files, so you do not have to deal with generating and pushing it manually. 

After grabbing needed metrics, send it to uploader (pushdata.py) by calling 
			
	jsondata.gen_data(name, timestamp, value, push.hostname, check_type,cluster_name)

Next push data to TSDB and truncate local copy: 

	jsondata.put_json()
	jsondata.truncate_data()

**Create scripts which calculates value rates :** 

	def run_checkname_rate()
	    sys.path.append(os.path.split(os.path.dirname(__file__))[0]+'/lib')
	    push = __import__('pushdata')
	    value_rate= __import__('record_rate')
	    rate=value_rate.ValueRate()
	    jsondata=push.JonSon()
	    jsondata.create_data()
	    name='some_metric'
	    value=10 # Values needed for calculations rate 
	    timestamp = int(datetime.datetime.now().strftime("%s"))
	    value_rate=rate.record_value_rate(key, value, timestamp)
		jsondata.gen_data(key, timestamp, value_rate, push.hostname, check_type, cluster_name)
	jsondata.put_json()
	jsondata.truncate_data()

**Create any scripts:**

To run custom script  like Bash, Perl etc.. Create scripts in format *check_name.extension* in folder scripts_enabled. 
All is needed from custom is to system out values in right order, Below is sample Bash scripts, which generates random number and send to collector for graphing:

	#!/bin/bash
		
	myvalue=$RANDOM
	mytype=random_gen
	check_type=my_bash_random
	check_style=stack
	
	myvalue2=$RANDOM
	mytype2=random_gen2
	check_type2=my_bash_random2
	check_style2=rate
	
	echo $mytype $myvalue $check_type $check_style
	echo -n $mytype2 $myvalue2 $check_type2 $check_style2

**Configuration:**

PuyPuy uses single ini file for self and metrics specific configurations. Configs are splitted into sections. 
Section [SelfConfig] contains base config parameters like checks interval, log/pid file location as well as some basic tags. 

    [SelfConfig]
    check_period_seconds: 5
    log_file: /tmp/puypuy.log
    pid_file: /tmp/puypuy.pid
    cluster_name: netangels
    host_group: testing

cluster_name and host_group are placeholders for tags for better manageability. Like if you need to tag web-servers of put web-servers in separate folder in Carbon. 

In section [TSDB] you should set correct backend and uri. 

OpenTSDB (Enable chinked requests in OpenTSDB )

opentsdb.conf

	tsd.http.request.enable_chunked = true

config.ini

OpenTSDB: OpenTSD does not supports authentication, but if you put it behind proxy and set basic auth everything will be fine  

	[TSDB]
	address: http://opentsdb_address:4242
	datapoints: /api/put
	user: netangels
	pass: bololo
	auth: False
	tsdtype: OpenTSDB

KairosDB: Enable or disable auth: in accordance to your KairosDB setup 
 
	[TSDB]
	address: http://kairosdb_address:8088
	datapoints: /api/v1/datapoints
	user: netangels
	pass: bololo
	auth: True
	tsdtype: KairosDB

InfluxDB: Enable or disable auth, but do not delete user/pass config params 

    [TSDB]
    address = http://influxdb_address:8086
    auth = False
    user = netangels
    pass = bololo
    database = test
    tsdtype = InfluxDB

Graphite Carbon: (PuyPuy uses Carbon pickle, default port is 2004)

	[TSDB]
	address: carbon_host:2004
	user: netangels
	pass: bololo
	auth: false
	tsdtype: Carbon

PuyPuy can work with only one backend at a time, so make sure that config file contains information about only one backend server/service.
PuyPuy is copletely stateless, so if you want to scale Backend, you can use any load balancing mechanism including DNS Round Robin.  
For all types of REST Backens (OpenTSDB, KairosDB, InfluxDB) config fiellds user/pass are mandatory even if you do not user authentication at backend.
So keep default paramaters as placeholders. 
