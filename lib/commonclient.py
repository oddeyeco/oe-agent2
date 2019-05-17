import pycurl
import socket
import lib.puylogger
import lib.pushdata


class CurlBuffer:
   def __init__(self):
       self.contents = ''

   def body_callback(self, buf):
       self.contents = self.contents + buf

def httpget(name, url, auth=None, headers=None):
    try:
        t = CurlBuffer()
        c = pycurl.Curl()
        c.setopt(c.URL, url)
        c.setopt(c.WRITEFUNCTION, t.body_callback)
        c.setopt(c.FAILONERROR, True)
        c.setopt(pycurl.USERAGENT, 'OddEye.co (Python agent)')
        c.setopt(pycurl.CONNECTTIMEOUT, 10)
        c.setopt(pycurl.TIMEOUT, 10)
        c.setopt(pycurl.NOSIGNAL, 5)
        if auth is not None:
            c.setopt(pycurl.USERPWD, auth)
        if headers is not None:
            c.setopt(pycurl.HTTPHEADER, [headers])
        c.perform()
        c.close()
        return t.contents
    except Exception as err:
        if name == 'check_oddeye':
            lib.pushdata.print_error(name, err)
        else:
            lib.puylogger.print_message(name + ' ' + str(err))
            lib.pushdata.print_error(name, err)


def socketget(name, buff, host, port, message):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((host, port))
        s.send(message)
        raw_data = s.recv(buff)
        s.close()
        return raw_data
    except Exception as err:
        lib.puylogger.print_message(name + ' ' + str(err))
        lib.pushdata.print_error(name, err)
