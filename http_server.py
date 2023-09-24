import socket
import threading
import time
'''
This server will mostly interacte up to the presntation layer, it will rarely handle aplication data.
The only time it will do stuff on the application layer will be for the HoneyPot that will be logged. This 
will mostly be for proxing requests to othere webservers I control.

I will try to add symetric key for every interaction between two hosts so no more then twe computers have a semetric key



'''


class server_verb_handler:
    PAGES = {'/':'html/home.html', '/test':'html/test.html'}

    def GET(self, path):
        if path in self.PAGES:
            with open(self.PAGES[path], 'r') as page:
                reutrun_data = page.read()
            return reutrun_data 
        else:
            return "HTTP/1.1 404 Not Found\n\n<h1>404 not found</h1>"

    def POST(self, path, data):
        if path in self.PAGES:
            with open(self.PAGES[path], 'r') as page:
                reutrun_data = page.read()
            return reutrun_data  
        else:
            return "HTTP/1.1 404 Not Found\n\n<h1>404 not found</h1>"



class server(server_verb_handler):
    def __init__(self, port):
        self.host = '0.0.0.0'
        self.port = port
        self.acceptable_useragents = ['python-requests/2.28.2']
        self.connections: list[object] = []
        self.max_connections: int = 10
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))


    def valide_useragent(self, headers) -> bool:
        return True
        '''
        for header in headers:
            if header.split("User-Agent: ")[-1] in self.acceptable_useragents:
                return True
        return False
        '''
    def parse_http_request(self, packet_data: bytes):
        parsed_headers: list[str] = [header.decode() for header in packet_data.split(b'\r\n')[:-1]]
        if not self.valide_useragent(parsed_headers):
            return False
        verb, uri, version = parsed_headers[0].split(' ')
        try:
            host = [host for host in parsed_headers if "Host: " in host][0].split('Host: ')[-1]
        except:
            raise Exception("No host header")
        
        if verb == "GET":
            return verb, uri, host, None
        elif verb == "POST":
            data = packet_data.split(b'\r\n')[-1]
            return verb, uri, host, data

    def client_handler(self, connection: object, address: tuple):
        #log ip, user agent, path, time
        try:
            self.connections.append(connection)
        except ConnectionResetError:
            self.connections.close()

        while True:
            try:
                http_request = connection.recv(1024)
            except OSError:
                connection.close()
                break
            if http_request:
                verb, uri, version, data = self.parse_http_request(http_request)
                
                if verb == "GET":
                    print(time.ctime(), address[0], verb, uri)#useragent
                    response = "HTTP/1.1 200 OK\nContent-type: text/html\nContent-length:"+str(len(self.GET(uri)))+"\nConnection: keep-alive\n\n"+self.GET(uri)
                    connection.send(bytes(response, 'utf-8'))
                elif verb == "POST":
                    print(time.ctime(), address[0], verb, uri, data)
                    response = "HTTP/1.1 200 OK\nContent-type: text/html\nContent-length:"+str(len(self.POST(uri, data)))+"\nConnection: keep-alive\n\n"+self.POST(uri, data)
                    connection.send(bytes(response, 'utf-8'))
                
                    
    def start(self):
        #this will listen for connections
        self.sock.listen(self.max_connections)

        while True:
            try:
                connection, address = self.sock.accept()

                threading.Thread(target = self.client_handler, args = (connection, address)).start()
            except KeyboardInterrupt:
                for conn in self.connections:
                    conn.close()
                    self.connections.remove(conn)
                break
        self.sock.close()
        exit()


web = server(8080)
web.start()