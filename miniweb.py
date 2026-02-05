import http.server
import os
import signal
import socket
import sys
import functools

# miniweb 3/2002 Alan Biocca
# Little Web Server. Serve files from a directory over HTTP.
#
# Revision History:
#   3.1  04Feb2026  Claude / Scott Hibbs KD4SIR - Prevent multiple instances.
#   3.0  27Jan2026  Claude / Scott Hibbs KD4SIR - Reliable LAN IP detection,
#        error handling, serve from specific directory, graceful shutdown.
#   2.0  21Jul2022  Scott Hibbs KD4SIR - Ported to Python 3.
#   1.8  12Jul2022  Scott Hibbs KD4SIR - Cleanup and restructuring.
#   1.7  27Jun2022  Scott Hibbs KD4SIR - Changed port (Win10 blocks 80).
#   1.6  17Jun2005  Alan Biocca - 2005-1 release.
#   1.5  21Jun2004  Alan Biocca - Minor adjustments.
#   1.4  21Jun2004  Alan Biocca - Comments added.

VERSION = "3.1"
PORT = 55555


def get_lan_ip():
    """Get the LAN IP address by connecting to a public DNS server."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        addr = s.getsockname()[0]
        s.close()
        return addr
    except OSError:
        return socket.gethostbyname(socket.gethostname())


def port_in_use(port):
    """Check if a port is already in use."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        s.bind(("", port))
        s.close()
        return False
    except OSError:
        return True


def serve(directory=None, port=PORT):
    """Start the HTTP server to serve files from the share directory."""
    if port_in_use(port):
        print(f"\n  MiniWeb is already running on port {port}.")
        print(f"  Only one instance is needed.\n")
        input("Press Enter to exit...")
        sys.exit(0)

    if directory is None:
        directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "share")
    directory = os.path.abspath(directory)

    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a directory. "
              f"\n\nPlease create a 'share' directory next to miniweb to share files.")
        input("\n\nPress Enter to exit...")
        sys.exit(1)

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=directory)
    handler.protocol_version = "HTTP/1.0"

    try:
        httpd = http.server.HTTPServer(("", port), handler)
    except OSError as e:
        print(f"Error: Could not start server on port {port}: {e}")
        input("Press Enter to exit...")
        sys.exit(1)

    hostname = socket.gethostname()
    lan_ip = get_lan_ip()

    print(f"\n  MiniWeb  Version: {VERSION}")
    print(f"  -------------------------\n")
    print(f"  Host:      {hostname} ({lan_ip})")
    print(f"  Serving:   {directory}")
    print(f"  Port:      {port}\n")
    print(f"  Browse to: http://{lan_ip}:{port}\n")
    print(f"  Press Ctrl+C to stop.\n")

    def shutdown_handler(sig, frame):
        print("\nShutting down.")
        httpd.server_close()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)

    httpd.serve_forever(poll_interval=0.5)


if __name__ == "__main__":
    # Optional: pass a directory as the first argument
    dir_arg = sys.argv[1] if len(sys.argv) > 1 else None
    serve(directory=dir_arg)
