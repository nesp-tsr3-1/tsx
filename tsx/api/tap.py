# JW - I'm not sure if all this code is necessary as twistd can already run a Flask app directly, e.g:
#
#     twistd --logfile=/var/log/tsxapi.log -n web --port tcp:8080 --wsgi tsx.api.api.app
#
# Log rotation could be handled by logrotate which is standard practice anyway
#
# So we could just change the init script, get rid of this file and the twisted/plugins directory, and
# everything would still work (I think).
#

import sys
import os

from twisted.application import internet, service
from twisted.web import server, resource, wsgi, static
from twisted.python import threadpool
from twisted.internet import reactor, ssl
from twisted.web import server, resource, client
from twisted.internet import defer
from twisted.python import usage
from twisted.python import log
import logging

import tsx.config

logger = logging.getLogger("tsxapi")
logger.setLevel(logging.DEBUG)


# Simple Threadpool class for Twisted
class ThreadPoolService(service.Service):
    def __init__(self, pool):
        self.pool = pool

    def startService(self):
        service.Service.startService(self)
        self.pool.start()

    def stopService(self):
        service.Service.stopService(self)
        self.pool.stop()


# Twisted Plugin CLI Options
class Options(usage.Options):
    optParameters = [["port", "p", "8080", "The port number to listen on."],
                     ["config","c",None,"Config file"]]


# Most settings can only be come from a config file
# If one is specified via the CLI, we'll use that, otherwise we'll check
# in /etc and in the current directory
# def read_config(clicfg):
#     config = ConfigParser.SafeConfigParser()
#     candidates = ['/opt/tsx/conf/tsxapi.conf','tsxapi.conf']
#     if clicfg['config'] != None:
#         candidates = [clicfg['config'],]
#     config.read(candidates)
#     if clicfg['port']:
#         if not config.has_section('Webservice'):
#             config.add_section('Webservice')
#         config.set('Webservice','Port',clicfg['port'])
#     return config


# Twisted Application Framework setup:

def makeService(cliconfig):
    application = service.Application('TSX API')

    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    observer = log.PythonLoggingObserver("tsxapi")
    observer.start()
    # config = read_config(cliconfig) # JW - disabling this for now
    # setup python logging

    log_file = tsx.config.get("api", "log_file", default = "/var/log/tsxapi.log")

    from logging.handlers import TimedRotatingFileHandler
    fh = TimedRotatingFileHandler(log_file, when='midnight',backupCount=7)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # read config file. this could do with some prettifying to give more
    # verbose feedback if a key isn't found.
    port = int(tsx.config.get("api", "port", default = 8080))
    logger.info("Using Port %d" % port)

    from tsx.api.api import app # TODO - make package naming less awkward

    # This bit is a workaround around a bug in Twisted.
    # If the threadpool is initialised before Twisted is daemonised, the
    # whole thing goes up in flames (sort of).
    # We avoid this by putting the multi-service in between.
    multi = service.MultiService()
    pool = threadpool.ThreadPool()
    tps = ThreadPoolService(pool)
    tps.setServiceParent(multi)
    resource = wsgi.WSGIResource(reactor, tps.pool, app)

    # Serve it up:
    main_site = server.Site(resource)
    internet.TCPServer(port, main_site).setServiceParent(multi)
    multi.setServiceParent(application)
    return multi

