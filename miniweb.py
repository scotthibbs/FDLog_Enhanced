import http.server
import socket
# miniweb 3/2002 Alan Biocca
# Little Web Server. Serve files in current dir and recursively below

print("\n\n\n  MiniWeb  Version: 2.0  21Jul2022")
print("  --------------------------------\n")

release_log = """

Revision 2.0 21Jul2022 Scott Hibbs KD4SIR
Preparing for FDLog_Enhanced in Python 3 for FD 2023
Ported to python 3 

Revision 1.8 12Jul2022 Scott Hibbs KD4SIR
Preparing for FDLog_Enhanced v2023
Removed unused sys import. Added instruction lines and a little restructuring. A little love for a little program.

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

hostname = socket.gethostname()
my_addr = socket.gethostbyname(hostname)

HandlerClass = http.server.SimpleHTTPRequestHandler
ServerClass = http.server.HTTPServer

protocol = "HTTP/1.0"
port = 55555
server_address = ('', port)
theaddr = str(my_addr)
theport = str(port)

HandlerClass.protocol_version = protocol
httpd = ServerClass(server_address, HandlerClass)
sa = httpd.socket.getsockname()

print(hostname, my_addr)
print("Serving HTTP on", "port", sa[1], "...\n")
print("Put a zip/tar in the same directory to share easily.")
print("On the same network, browse to %s:%s\n" % (theaddr, theport))
print("Close this window to terminate...")
httpd.serve_forever()
