import os, sys
import ConfigParser
import pycurl
import pushdata

config = ConfigParser.RawConfigParser()
config.read(os.path.split(os.path.dirname(__file__))[0]+'/conf/config.ini')
tmpdir = config.get('SelfConfig', 'tmpdir')
tsdb_type = config.get('TSDB', 'tsdtype')

c = pycurl.Curl()

if tsdb_type == 'OddEye':
    tsdb_url = config.get('TSDB', 'url')
if tsdb_type == 'InfluxDB':
    tsdb_url = pushdata.influx_url
    if pushdata.curl_auth is True:
        c.setopt(pycurl.USERPWD, pushdata.influx_auth)
if pushdata.tsd_rest is True:
    tsdb_url = pushdata.tsdb_url
    if pushdata.curl_auth is True:
        c.setopt(pycurl.USERPWD, pushdata.tsdb_auth)

# import httplib
# def upload_files(myfile):
#     http_response_codes = [100, 101, 102, 200, 201, 202, 203, 204, 205, 206, 207, 208, 226, 300, 301, 302, 303, 304, 305, 306, 307, 308]
#     if myfile.endswith(".cached"):
#         try:
#             filepath = tmpdir + '/' + myfile
#             content = open(filepath, "r").read()
#             con = httplib.HTTPSConnection('barlus.oddeye.co')
#             con.request("POST", "/oddeye-barlus/put/tsdb", content, headers={"Connection": " keep-alive"})
#             try:
#                 response_code = int(con.getresponse().status)
#             except:
#                 pass
#             if response_code in http_response_codes:
#                 os.remove(filepath)
#                 return True
#             else:
#                 return False
#         except Exception as e:
#             pushdata.print_error(e, 'from cache uploader')
#             return False
#             pass

def upload_files(myfile):
    http_response_codes = [100, 101, 102, 200, 201, 202, 203, 204, 205, 206, 207, 208, 226, 300, 301, 302, 303, 304, 305, 306, 307, 308]
    if myfile.endswith(".cached"):
        try:
            filepath = tmpdir + '/' + myfile
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
                return True
            else:
                return False
        except Exception as e:
            pushdata.print_error(e, 'from cache uploader')
            return False
            pass


def cache_uploader():
    for myfile in os.listdir(tmpdir):
    #for myfile in sorted(os.listdir(tmpdir)):
        if upload_files(myfile) is not True:
            break
