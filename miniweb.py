# miniweb 3/2002 akb

# little web server

# run by double clicking or from cmd window
# serves files in current dir and recursively below

print "\nMiniWeb $Revision: 1.6 $ $Date: 2005/06/17 23:56:23 $ \n\n"

release_log = """\

$Log: miniweb.py,v $

Revision 1.7 27Jun2022 Scott Hibbs KD4SIR
Preparing for FDLog_Enhanced v2023
Had to change ports as Win10 blocks 80. 

Revision 1.6  2005/06/17 23:56:23  Alan Biocca
Preparing for 2005-1 release.

Revision 1.5  2004/06/21 04:43:39  Administrator
Updating plans from email comments. blank space adjusted on miniweb. akb.

Revision 1.4  2004/06/21 04:40:22  Administrator
Comments added. akb.
"""

import BaseHTTPServer, SimpleHTTPServer, socket, sys

hostname = socket.gethostname()
my_addr = socket.gethostbyname(hostname)

print hostname, my_addr

HandlerClass = SimpleHTTPServer.SimpleHTTPRequestHandler
ServerClass = BaseHTTPServer.HTTPServer

protocol="HTTP/1.0"
port = 55555
server_address = ('', port)

HandlerClass.protocol_version = protocol
httpd = ServerClass(server_address, HandlerClass)

sa = httpd.socket.getsockname()
print "Serving HTTP on", "port", sa[1], "..."
print "Close this window to terminate..."
httpd.serve_forever()

#eof

