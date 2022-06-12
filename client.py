import re
import socket
import sys


class FTPClient:
    def __init__(self, ip_address, c_port, d_port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip_address = ip_address
        self.control_port = c_port
        self.data_port = d_port
        self.ds = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def createConnection(self):
        print('Starting connection to {}:{}'.format(self.ip_address, ':', self.control_port))
        try:
            server_address = (self.ip_address, self.control_port)
            self.s.connect(server_address)
            print('Connected to {} : {}'.format(self.ip_address, self.control_port))
        except KeyboardInterrupt:
            self.close_client()
        except:
            print('Connection to {} : {} failed'.format(self.ip_address, self.control_port))
            self.close_client()

    def start(self):
        global command, path
        try:
            self.createConnection()
        except Exception as e:
            self.close_client()
            quit()

        while True:
            try:
                command = input('Enter command: ')
                if not command:
                    print('Need a command.')
                    continue
            except KeyboardInterrupt:
                self.close_client()

            if " " in command:
                cmd = command.split(" ")[0]
                path = command.split(" ")[1]
            else:
                cmd = command

            try:
                self.s.sendall(command.encode('UTF-8'))
                data = self.s.recv(1024).decode()
                print(data)

                if cmd.upper() in ('QUIT', 'BYE', 'CLOSE'):
                    self.close_client()
                elif cmd.upper() in ('LS'):
                    if data and (data[0:3] == '125'):
                        func = getattr(self, cmd.upper())
                        func()
                        data = self.s.recv(1024).decode()
                        print(data)
                elif cmd.upper() in ('PUT', 'GET'):
                    if data and (data[0:3] == '125'):
                        func = getattr(self, cmd.upper())
                        func(path)
                        data = self.s.recv(1024).decode()
                        print(data)
                self.ds.close()
                self.ds = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            except Exception as e:
                print(str(e))
                self.close_client()

    def connectDataSocket(self):
        self.ds.connect((self.ip_address, self.data_port))

    def LS(self):
        try:
            self.connectDataSocket()
            while True:
                dirList = self.ds.recv(1024).decode()
                if not dirList:
                    break
                sys.stdout.write(str(dirList))
                sys.stdout.flush()
        except Exception as e:
            print(str(e))

    def PUT(self, path):
        global f
        print('Storing', path, 'to the server')
        try:
            self.connectDataSocket()
            f = open(path, 'r')
            upload = f.read(1024)
            while upload:
                self.ds.sendall(upload.encode('UTF-8'))
                upload = f.read(1024)
        except Exception as e:
            print(str(e))
        finally:
            f.close()
            self.ds.close()

    def GET(self, path):
        global f
        print('Retrieving', path, 'from the server')
        try:
            self.connectDataSocket()
            f = open(path, 'w')
            while True:
                download = self.ds.recv(1024).decode()
                if not download: break
                f.write(str(download))
        except Exception as e:
            print(str(e))
        finally:
            f.close()
            self.ds.close()

    # stop FTP client, close the connection and exit the program
    def close_client(self):
        print('Closing socket connection...')
        self.s.close()
        print('FTP client terminating...')
        quit()


if __name__ == "__main__":
    '''try:
        pat = re.compile(
            "^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$")
        address = input("Destination address\n")
        if not pat.search(address):
            raise Exception()
    except Exception:
        print("Enter Valid Address\n")
        quit()

    try:
        c_port = input("Enter Command Connection Port No.\n")
        d_port = input("Enter Data Connection Port No.\n")
        if not c_port:
            c_port = 21
        else:
            c_port = int(c_port) % 65535
        if not d_port:
            d_port = 20
        else:
            d_port = int(d_port) % 65535
    except ValueError:
        print("Enter Valid Port Number\n")
        quit()'''
    address = '127.0.0.1'
    c_port=21
    d_port=20
    ftpClient = FTPClient(address, c_port, d_port)
    ftpClient.start()
