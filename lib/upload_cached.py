import os
import pycurl
import lib.pushdata
import lib.getconfig
import lib.puylogger

tmpdir = lib.getconfig.getparam('SelfConfig', 'tmpdir')
tsdb_type = lib.getconfig.getparam('TSDB', 'tsdtype')

c = pycurl.Curl()

if tsdb_type == 'OddEye':
    tsdb_url = lib.getconfig.getparam('TSDB', 'url')
if tsdb_type == 'InfluxDB':
    tsdb_url = lib.pushdata.influx_url
    if lib.pushdata.curl_auth is True:
        c.setopt(pycurl.USERPWD, lib.pushdata.influx_auth)
if lib.pushdata.tsd_rest is True:
    tsdb_url = lib.pushdata.tsdb_url
    if lib.pushdata.curl_auth is True:
        c.setopt(pycurl.USERPWD, lib.pushdata.tsdb_auth)

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
                lib.puylogger.print_message('Cache Uploader: ' + filepath + ' file processed')
                return True
            else:
                return False
        except Exception as e:
            lib.pushdata.print_error(e, 'from cache uploader')
            return False
            pass


def cache_uploader():
    for myfile in os.listdir(tmpdir):
        if upload_files(myfile) is not True:
            break
