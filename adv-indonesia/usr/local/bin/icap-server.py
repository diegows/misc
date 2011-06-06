from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor

from tempfile import NamedTemporaryFile

from syslog import openlog, syslog
import os
import pdb
import re
import zlib
import gzip
import sys

import ConfigParser

config = ConfigParser.RawConfigParser()
config.read(sys.argv[1])

bind_to = config.get('icap-server', 'bind')
port = config.get('icap-server', 'port')
css_url = config.get('icap-server', 'css_url')
js_url = config.get('icap-server', 'js_url')
spool_dir = config.get('icap-server', 'spool_dir')


OPTIONS_RESP = """ICAP/1.0 200 OK\r
Service: icap-server.py\r
ISTag: icap-server-001\r
Options-TTL: 3600\r
Encapsulated: opt-body=0\r
Methods: RESPMOD\r
Transfer-Complete: *\r
\r
"""

RESPMOD_RESP = """ICAP/1.0 200 OK\r
Server: icap-server.py\r
Connection: close\r
ISTag: icap-server-001\r
Encapsulated: res-hdr=0, %s=%d\r
\r
"""

AD_HEAD = re.compile ('(?P<pre>.*<\s*HEAD[^<]*>)(?P<post>.*)',
                re.IGNORECASE | re.MULTILINE | re.DOTALL)

JS_HEAD = """
<link rel="stylesheet" type="text/css" href="%s">
<script type="text/javascript"
src="http://ajax.googleapis.com/ajax/libs/jquery/1.6.1/jquery.min.js"></script>
<script type="text/javascript" src="%s"></script>
""" % (css_url, js_url)

class HeaderError:
    FIRST_LINE = 'First line invalid'
    HEADER = 'Header error'
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class ICAP(LineReceiver):
    CONTENT_LENGTH = 'content-length'
    CONTENT_ENCODING = 'content-encoding'
    ENCAPSULATED = 'encapsulated'
    REQ_HDR = 'req-hdr'
    REP_HDR = 'rep-hdr'
    RES_BODY = 'res-body'
    NULL_BODY = 'null-body'
    GZIP = 'gzip'
    REFERER = 'referer'

    def connectionMade(self):
        self.headers = {}
        self.first_line = False
        self.length = 0
        self.body = False
        self.headers_body = 0
        self.chunk = 0
        self.content_encoding = False
        self.descompressor = False
        self.referer = False
        self.temp_files = []

    def lineReceived(self, line):
        try:
            if self.body:
                self.read_body(line)
            elif line == '':
                self.headersReceived()
            elif not self.first_line:
                self.first_line = self.parse_first_line(line)
            else:
                self.parse_header_add(line)

        except HeaderError, e:
            syslog('ERROR: ' + str(e) + ', ' + str(self.first_line))
            self.error(e)

        #self.sendLine(line)

    def headersReceived(self):
        if self.first_line[0] == 'RESPMOD':
            self.do_RESPMOD()
        elif self.first_line[0] == 'OPTIONS':
            self.do_OPTIONS()
        else:
            raise HeaderError("Invalid method.")

    def parse_first_line(self, line):
        parts = line.split()
        if len(parts) != 3:
            raise HeaderError(HeaderError.FIRST_LINE)

        return parts

    def parse_header(self, line):
        i = line.find(':')
        if i < 0:
            self.transport.loseConnection()

        header = line[:i]
        value = line[i+1:].lstrip()

        return [ header, value ]

    def parse_header_add(self, line):
        header = self.parse_header(line)
        self.headers[header[0].lower()] = header[1]

    def setLength(self):
        self.length = int(self.headers[self.CONTENT_LENGTH])

    def rawDataReceived(self, data):
        if self.chunk == -1:
            raise HeaderError('Excess data.')

        #if self.descompressor:
        #    data = self.descompressor.decompress(data)
            
        data_len = len(data)
        while data_len > 0:
            if self.chunk == 0:
                crlf_pos = data.find(self.delimiter)
                self.chunk = int(data[:crlf_pos], 16)
                if self.chunk == 0:
                    self.chunk = -1
                    self.finish_RESPMOD()
                    return

                data = data[crlf_pos + 2:]
                data_len = len(data)

            if data_len > self.chunk:
                self.tmp_fd.write(data[:self.chunk])
                data = data[self.chunk:]
                data_len -= self.chunk
                self.chunk = 0
            else:
                self.tmp_fd.write(data)
                self.chunk -= data_len
                data_len = 0

            if self.chunk < 0:
                raise HeaderError('Chunk data is negative.')

            if self.chunk == 0 and data_len > 0:
                data = data[2:]
                data_len -= 2

    def do_OPTIONS(self):
        self.transport.write(OPTIONS_RESP)

    def do_RESPMOD(self):
        if not self.ENCAPSULATED in self.headers.keys():
            raise HeaderError(self.ENCAPSULATED + ' header missing')

        self.parse_encap()
        self.tmp_fd = NamedTemporaryFile(delete = False, dir = spool_dir)
        self.temp_files.append(self.tmp_fd.name)
        self.body = True

    def read_body(self, line):
        self.tmp_fd.write(line + self.delimiter)

        if line.lower().startswith(self.CONTENT_ENCODING):
            self.parse_content_encoding(line)

        if line.lower().startswith(self.REFERER):
            self.referer = self.parse_header(line)[1]

        if line == '':
            self.headers_body += 1

        if self.headers_body == 2:
            if self.has_body():
                self.setRawMode()
            else:
                self.finish_RESPMOD()

    def finish_RESPMOD(self):
        self.tmp_fd.seek(self.encap['res-hdr'], os.SEEK_SET)
        encap_hdr = ''
        while True:
            line = self.tmp_fd.readline()
            if not line:
                return

            if line.lower().startswith(self.CONTENT_LENGTH):
                continue

            encap_hdr += line

            if line == self.delimiter:
                break

        if not self.has_body():
            encap_attr = self.NULL_BODY
            encap_body = None
        else:
            encap_attr = self.RES_BODY
            encap_body = self.get_encap_body()
            encap_body_size = len(encap_body)
            encap_body = str(encap_body_size) + self.delimiter + encap_body
            #0 Removed by now. There is a bug somewhere.
            encap_body += self.delimiter + ' ' + self.delimiter

        encap_hdr_size = len(encap_hdr)
        respmod_resp_hdr = RESPMOD_RESP % (encap_attr, encap_hdr_size)

        self.transport.write(respmod_resp_hdr)
        self.transport.write(encap_hdr)
        if encap_body:
            self.transport.write(encap_body)
        self.transport.loseConnection()

    def get_encap_body(self):
        encap_body = self.tmp_fd.read()
        #uncompress if the body is gzipped
        if self.descompressor == None:
            return encap_body
        elif self.descompressor:
            zipped = NamedTemporaryFile(delete = False, dir = spool_dir)
            self.temp_files.append(zipped.name)
            zipped.write(encap_body)
            zipped.flush()
            g = gzip.GzipFile(zipped.name)
            encap_body = g.read()

        try:
            ad_head = AD_HEAD.match(encap_body)

            if ad_head:
                pre = ad_head.group('pre')
                post = ad_head.group('post')
                encap_body = pre + JS_HEAD + post

        except:
            syslog('ERROR: applying regex' + str(self.first_line))

        #compress it again
        if self.descompressor:
            f_out = NamedTemporaryFile(delete = False, dir = spool_dir)
            self.temp_files.append(f_out.name)
            f_out.close()
            f_out = gzip.open(f_out.name, 'wb')
            name = f_out.name
            f_out.write(encap_body)
            f_out.close()
            encap_body = open(name).read()

        return encap_body

    def has_body(self):
        return (not self.NULL_BODY in self.encap.keys())

    def parse_encap(self):
        encap = self.headers[self.ENCAPSULATED].replace(' ', '').split(',')

        self.encap = {}
        for offset in encap:
            try:
                attr, value = offset.split('=')
                self.encap[attr] = int(value)
            except:
                raise HeaderError(self.ENCAPSULATED + ' malformed: ' + \
                                    str(encap))

    def parse_content_encoding(self, line):
        content_encoding = self.parse_header(line)
        if content_encoding[1].lower() == self.GZIP:
            self.descompressor = zlib.decompressobj()
            self.content_encoding = True
        else:
            self.descompressor = None

    def error(self, msg):
        self.transport.write("HTTP/1.1 400 Bad Request\r\n\r\n%s\r\n" % \
                                (str(msg)))

    def connectionLost(self, reason = None):
        #Remove temp files
        for file in self.temp_files:
            os.unlink(file)


#main()

def main():
    openlog('icap-server.py')

    icap_factory = Factory()
    icap_factory.protocol = ICAP

    reactor.listenTCP(int(port), icap_factory, interface = bind_to)
    reactor.run()

while True:
    pid = os.fork()
    if not pid:
        main()
        break

    os.waitpid(pid, 0)
    syslog('Child process died: ' + str(pid))

