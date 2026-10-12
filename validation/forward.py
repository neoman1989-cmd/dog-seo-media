"""Optional loopback bridge for cloud machines with a separate Docker namespace."""
import argparse
import socket
import socketserver
import threading
parser=argparse.ArgumentParser()
parser.add_argument('container_ip')
args=parser.parse_args()
class Forward(socketserver.BaseRequestHandler):
    def handle(self):
        with socket.create_connection((args.container_ip,80),timeout=10) as upstream:
            def pump(source,destination):
                try:
                    while chunk:=source.recv(65536): destination.sendall(chunk)
                except OSError: pass
                finally:
                    try: destination.shutdown(socket.SHUT_WR)
                    except OSError: pass
            thread=threading.Thread(target=pump,args=(self.request,upstream)); thread.start()
            pump(upstream,self.request); thread.join()
class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address=True
with Server(('127.0.0.1',8080),Forward) as server: server.serve_forever()
