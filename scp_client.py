import sys
import os
import traceback

import logging
from logging import handlers

import paramiko

logging.getLogger("paramiko").setLevel(logging.WARNING)
logger = logging.getLogger()

fileHandler = logging.handlers.TimedRotatingFileHandler('log/scp_client.log','d', 10)
loggerHandlerFormatter = logging.Formatter('%(asctime)s.%(msecs)03d [%(levelname)s] %(message)s',
                                           datefmt='%Y-%m-%d %H:%M:%S')
fileHandler.setFormatter(loggerHandlerFormatter)
fileHandler.setLevel(logging.DEBUG)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(loggerHandlerFormatter)
consoleHandler.setLevel(logging.DEBUG)

logger.addHandler(fileHandler)
logger.addHandler(consoleHandler)

logger.setLevel(logging.INFO)

def getCurrentPath():
    if getattr(sys, 'frozen', False):
        # frozen
        current_path = os.path.dirname(sys.executable)
        return current_path
    else:
        # unfrozen
        current_path = os.path.dirname(os.path.realpath(__file__))
        return current_path

current_path = getCurrentPath()
filekey = os.path.join(current_path,'key/test@local.ppk.ssh')

class SCPClient:
    def __init__(self):
        try:
            self.hostname = 'localhost'
            self.port = 22
            self.username = 'test'
            self.password = 'user.test'
            self.key = paramiko.RSAKey.from_private_key_file(filekey, self.password)
        except Exception as e:
            logging.error('Caught exception: %s: %s' % (e.__class__, e))
            sys.exit(1)

    def connect(self):
        try:
            self.sshclient = paramiko.SSHClient()
            self.sshclient.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.sshclient.connect(self.hostname, self.port, self.username,'', self.key)
            return True
        except Exception as e:
            logging.error("Caught exception: {}: {}".format(e.__class__, e))
            try:
                self.sshclient.close()
            except:
                pass
            sys.exit(1)
            return False

    def getNewFiles(self):
        if self.connect():
            curFileList = 'cache/lastFileList.tmp'
            try:
                with open(curFileList, 'r') as file:
                    curFiles = file.read().splitlines()
            except Exception as e:
                if str(e.__class__) == "<class 'FileNotFoundError'>":
                    with open(curFileList, 'w') as file:
                        file.write("")
                else:
                    logging.error("Caught exception: {}: {}.".format(e.__class__, e))
                    sys.exit(1)

            remotepath = '/srv/mbr/images/'
            localpath = 'cache/images/'
            try:
                self.sftpclient = self.sshclient.open_sftp()
                newFiles = self.sftpclient.listdir(remotepath)
            except Exception as e:
                logging.error("Caught exception: {}: {}.".format(e.__class__, e))
                sys.exit(1)

            scurFiles = set(curFiles)
            diffFiles = [x for x in newFiles if x not in scurFiles]
            if diffFiles:
                try:
                    with open(curFileList, 'w') as file:
                        for filename in newFiles:
                         file.write("{}\n".format(filename))
                    for file in diffFiles:
                        self.sftpclient.get(remotepath + file, localpath + file)
                        logging.info('Add file to mbr - {}.'.format(file))
                except Exception as e:
                    logging.error("Caught exception: {}: {}.".format(e.__class__, e))
            self.sftpclient.close()
            self.sshclient.close()
            logging.info("Opened SSH connection closed.")

def main():
    scpclient = SCPClient()
    scpclient.getNewFiles()
    sys.exit(0)

if __name__ == "__main__":
    main()