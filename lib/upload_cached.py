import os, sys
import ConfigParser
import pycurl
import pushdata


config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
tmpdir = config.get('SelfConfig', 'tmpdir')
tsdb_type= config.get('TSDB', 'tsdtype')

c = pycurl.Curl()

if (tsdb_type == 'OddEye'):
    tsdb_url = config.get('TSDB', 'url')
if (tsdb_type == 'InfluxDB'):
    tsdb_url = pushdata.influx_url
    if pushdata.curl_auth is True:
        c.setopt(pycurl.USERPWD, pushdata.influx_auth)
if pushdata.tsd_rest is True:
    tsdb_url = pushdata.tsdb_url
    if pushdata.curl_auth is True:
        c.setopt(pycurl.USERPWD, pushdata.tsdb_auth)

def cache_uploader():
    http_response_codes = [100, 101, 102, 200, 201, 202, 203, 204, 205, 206, 207, 208, 226, 300, 301, 302, 303, 304, 305, 306, 307, 308]
    for file in os.listdir(tmpdir):
        if file.endswith(".cached"):
            try:
                filepath = tmpdir + '/' + file
                content = open(filepath, "r").read()
                c.setopt(pycurl.URL, tsdb_url)
                c.setopt(pycurl.POST, 1)
                c.setopt(pycurl.VERBOSE, 0)
                c.setopt(pycurl.TIMEOUT, 10)
                c.setopt(pycurl.NOSIGNAL, 5)
                c.setopt(pycurl.WRITEFUNCTION, lambda x: None)
                c.setopt(pycurl.USERAGENT, 'Cacher PuyPuy v.0.2')
                c.setopt(pycurl.POSTFIELDS, content)
                c.perform()
                try:
                    response_code = int(c.getinfo(pycurl.RESPONSE_CODE))
                except:
                    pass
                if response_code in http_response_codes:
                    os.remove(filepath)

            except Exception as e:
                push = __import__('pushdata')
                push.print_error(e, 'from cache uploader')
                pass


