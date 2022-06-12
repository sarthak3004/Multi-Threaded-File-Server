import os
import socket
import threading
import time


class FTPThreadServer(threading.Thread):
    def __init__(self, client, local_ip, data_port):
        self.client = client[0]
        self.client_address = client[1]
        self.cwd = os.getcwd()
        self.data_address = (local_ip, data_port)
        self.ds = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        threading.Thread.__init__(self)

    def startDataSocket(self):
        try:
            print('Creating Data Socket on a {}'.format(str(self.data_address)))
            self.ds.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.ds.bind(self.data_address)
            self.ds.listen(5)
            print('Data socket is started. Listening to {}'.format(str(self.data_address)))
            self.client.sendall(b'125 Data connection already open; transfer starting.\r\n')
            return self.ds.accept()
        except Exception as e:
            print("Error:"+str(e))
            self.closeDataSocket()
            self.client.sendall(b'425 Cannot open data connection.\r\n')

    def closeDataSocket(self):
        print("Data Connection with {} Closed ".format(str(self.data_address)))
        self.ds.close()
        self.ds = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):
        try:
            print("run\n")
            print('Client Connected: {}\n'.format(str(self.client_address)))

            while True:
                cmd = self.client.recv(1024).decode()
                if not cmd:
                    break
                print('Command from {}:{}'.format(str(self.client_address),cmd))
                try:
                    func = getattr(self, cmd.split(" ")[0].upper())
                    func(cmd)
                except AttributeError as e:
                    print('ERROR: {} :Invalid Command.'.format(str(self.client_address)))
                    self.client.sendall(b'550 Invalid Command\r\n')
        except Exception as e:
            print('ERROR: ' + str(self.client_address) + ': ' + str(e))
            self.QUIT('')

    def QUIT(self, cmd):
        try:
            self.client.sendall(b'221 Goodbye.\r\n')
        except:
            pass
        finally:
            print('Closing connection from ' + str(self.client_address) + '...')
            self.closeDataSocket()
            self.client.close()
            quit()
    def BYE(self, cmd):
        try:
            self.client.sendall(b'221 Goodbye.\r\n')
        except:
            pass
        finally:
            print('Closing connection from ' + str(self.client_address) + '...')
            self.closeDataSocket()
            self.client.close()
            quit()

    def CLOSE(self, cmd):
        try:
            self.client.sendall(b'221 Goodbye.\r\n')
        except:
            pass
        finally:
            print('Closing connection from ' + str(self.client_address) + '...')
            self.closeDataSocket()
            self.client.close()
            quit()

    def LS(self, cmd):
        print('LIST', self.cwd)
        (client_data, client_address) = self.startDataSocket()

        try:
            listdir = os.listdir(self.cwd)
            if not len(listdir):
                max_length = 0
            else:
                max_length = len(max(listdir, key=len))

            header = '| %*s | %9s | %12s | %20s | %11s | %12s |' % (max_length, 'Name', 'Filetype', 'Filesize', 'Last Modified', 'Permission', 'User/Group')
            table = '%s\n%s\n%s\n' % ('-' * len(header), header, '-' * len(header))
            client_data.sendall(table.encode('UTF-8'))

            for i in listdir:
                path = os.path.join(self.cwd, i)
                stat = os.stat(path)
                data = '| %*s | %9s | %12s | %20s | %11s | %12s |\n' % (max_length, i, 'Directory' if os.path.isdir(path) else 'File', str(stat.st_size) + 'B',time.strftime('%b %d, %Y %H:%M', time.localtime(stat.st_mtime)), oct(stat.st_mode)[-4:], str(stat.st_uid) + '/' + str(stat.st_gid))
                client_data.sendall(data.encode('UTF-8'))

            table = '%s\n' % ('-' * len(header))
            client_data.sendall(table.encode('UTF-8'))

            self.client.sendall(b'\r\n226 Directory send OK.\r\n')
        except Exception as e:
            print('ERROR: ' + str(self.client_address) + ': ' + str(e))
            self.client.sendall(b'426 Connection closed; transfer aborted.\r\n')
        finally:
            client_data.close()
            self.closeDataSocket()

    def PWD(self, cmd):
        self.client.sendall(b'257 \"' + self.cwd.encode('UTF-8')+b'\".\r\n')

    def CD(self, cmd):
        dest = os.path.join(self.cwd, cmd.split(" ")[1])
        if os.path.isdir(dest):
            self.cwd = dest
            self.client.sendall(b'250 OK \"'+self.cwd.encode('UTF-8')+b'\".\r\n')
        else:
            print('ERROR: ' + str(self.client_address) + ': No such file or directory.')
            self.client.sendall(b'550 \"' + dest.encode('UTF-8') + b'\": No such file or directory.\r\n')

    def CDUP(self, cmd):
        dest = os.path.abspath(os.path.join(self.cwd, '..'))
        if os.path.isdir(dest):
            self.cwd = dest
            self.client.sendall(b'250 OK \"'+self.cwd.encode('UTF-8')+b'\".\r\n')
        else:
            print('ERROR: ' + str(self.client_address) + ': No such file or directory.')
            self.client.sendall(b'550 \"' + dest.encode('UTF-8') + b'\": No such file or directory.\r\n')

    def MKDIR(self, cmd):
        path = cmd.split(" ")[1]
        dirname = os.path.join(self.cwd, path)
        try:
            if not path:
                self.client.sendall(b'501 Missing arguments <dirname>.\r\n')
            else:
                os.mkdir(dirname)
                self.client.sendall(b'250 Directory created: ' + dirname.encode('UTF-8') + b'.\r\n')
        except Exception as e:
            print('ERROR: ' + str(self.client_address) + ': ' + str(e))
            self.client.sendall(b'550 Failed to create directory ' + dirname.encode('UTF-8') + b'.')

    def RMDIR(self, cmd):
        path = cmd.split(" ")[1]
        dirname = os.path.join(self.cwd, path)
        try:
            if not path:
                self.client.sendall(b'501 Missing arguments <dirname>.\r\n')
            else:
                os.rmdir(dirname)
                self.client.sendall(b'250 Directory deleted: ' + dirname.encode("UTF-8") + b'.\r\n')
        except Exception as e:
            print('ERROR: ' + str(self.client_address) + ': ' + str(e))
            self.client.sendall(b'550 Failed to delete directory ' + dirname.encode('UTF-8') + b'.')

    def DELETE(self, cmd):
        path = cmd.split()[1]
        filename = os.path.join(self.cwd, path)
        try:
            if not path:
                self.client.sendall(b'501 Missing arguments <filename>.\r\n')
            else:
                os.remove(filename)
                self.client.sendall(b'250 File deleted: ' + filename.encode('UTF-8') + b'.\r\n')
        except Exception as e:
            print('ERROR: ' + str(self.client_address) + ': ' + str(e))
            self.client.sendall(b'550 Failed to delete file ' + filename.encode('UTF-8') + b'.')

    def PUT(self, cmd):
        global file_write
        path = cmd.split(" ")[1]
        if not path:
            self.client.sendall(b'501 Missing arguments <filename>.\r\n')
            return

        fname = os.path.join(self.cwd, path)
        (client_data, client_address) = self.startDataSocket()

        try:
            file_write = open(fname, 'w')
            while True:
                data = client_data.recv(1024).decode()
                if not data:
                    break
                file_write.write(data)

            self.client.sendall(b'226 Transfer complete.\r\n')
        except Exception as e:
            print('ERROR: ' + str(self.client_address) + ': ' + str(e))
            self.client.sendall('b425 Error writing file.\r\n')
        finally:
            client_data.close()
            self.closeDataSocket()
            file_write.close()

    def GET(self, cmd):
        global file_read
        path = cmd.split()[1]
        if not path:
            self.client.sendall(b'501 Missing arguments <filename>.\r\n')
            return

        fname = os.path.join(self.cwd, path)
        (client_data, client_address) = self.startDataSocket()
        if not os.path.isfile(fname):
            self.client.sendall(b'550 File not found.\r\n')
        else:
            try:
                file_read = open(fname, "r")
                data = file_read.read(1024)

                while data:
                    client_data.sendall(data.encode('UTF-8'))
                    data = file_read.read(1024)

                self.client.sendall(b'226 Transfer complete.\r\n')
            except Exception as e:
                print('ERROR: ' + str(self.client_address) + ': ' + str(e))
                self.client.sendall(b'426 Connection closed; transfer aborted.\r\n')
            finally:
                client_data.close()
                self.closeDataSocket()
                file_read.close()



class FTPServer:
    def __init__(self, control_port, data_port):
        self.address = '0.0.0.0'
        self.control_port = control_port
        self.data_port = data_port
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def createSocket(self):
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_address = (self.address, self.control_port)

        try:
            print("Creating Socket on {}:{}\n".format(self.address, self.control_port))
            self.s.bind(server_address)
            self.s.listen(5)
            print("Server listening on {}:{}\n".format(self.address, self.control_port))
        except Exception as e:
            print("Failed : {}\n".format(str(e)))
            quit()

    def start(self):
        self.createSocket()

        try:
            while True:
                print("Waiting for a connection")
                thread = FTPThreadServer(self.s.accept(), self.address, self.data_port)
                thread.daemon = True
                thread.start()
        except KeyboardInterrupt:
            print('Closing')
            self.s.close()
            quit()


if __name__ == "__main__":

    try:
        #c_port = input("Enter Command Connection Port No.\n")
        #d_port = input("Enter Data Connection Port No.\n")
        # if not c_port:
            c_port = 21
        # else:
        #     c_port = int(c_port) % 65535
        # if not d_port:
            d_port = 20
        # else:
        #     d_port = int(d_port) % 65535
    except ValueError:
        print("Enter Valid Port Number\n")
        quit()
    obj = FTPServer(c_port, d_port)
    obj.start()

