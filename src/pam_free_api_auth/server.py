from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from urllib2 import urlopen
from ssl import wrap_socket
from threading import currentThread

class Server:

    class HTTPServerReuseAddress(HTTPServer):
        allow_reuse_address = True

    def __init__(self, port, auth_uuid):
        self.port = port
        self.httpd = self.HTTPServerReuseAddress(('', self.port), self.getHandler())
        self.httpd.socket = wrap_socket(self.httpd.socket,
            keyfile="/etc/ssl/private/pam-free-api-auth.key",
            certfile="/etc/ssl/certs/pam-free-api-auth.cert",
            server_side=True)
        self.generated_uuid = auth_uuid
        self.auth_success = False

    def getHandler(self):
        class Handler(BaseHTTPRequestHandler, object):
            def log_message(self_Handler, *args, **kwargs):
                pass

            def do_GET(self_Handler):
                if self_Handler.path == "/" + self.generated_uuid:
                    self.auth_success = True
                    self_Handler.send_response(202)
                    self_Handler.end_headers()
                    self_Handler.wfile.write(b'Welcome Captain!')
                else:
                    self_Handler.send_response(451)
                    self_Handler.end_headers()
                    self_Handler.wfile.write(b'You are attempting to access a secured resource. This request will lead to further investigation.')

        return Handler

    def run(self):
        t = currentThread()
        while not getattr(t, "should_stop", False) and not self.auth_success:
            self.httpd.handle_request()

    def close(self):
        """
        Forcing a last call to circumvent self.httpd.handle_request blocking behavioue.
        Then effectively close the server resource to free the port.
        """
        response = None
        try:
            response = urlopen("https://127.0.0.1:{}/".format(self.port), timeout = 1)
        except:
            pass
        finally:
            if response:
                response.close()
        self.httpd.server_close()