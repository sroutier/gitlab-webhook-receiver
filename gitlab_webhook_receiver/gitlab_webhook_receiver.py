#!/usr/bin/python -tt
#
# Copyright (C) 2012 Shawn Sterling <shawn@systemtemplar.org>
#               2016 Guillaume Espanel <guillaume.espanel@objectif-libre.com>
#               2017 Sebastien Routier <sroutier@gmail.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
#
# gitlab-webhook-receiver: a script for gitlab & puppet integration
#
# The latest version of this code will be found on my github page:
# https://github.com/shawn-sterling/gitlab-webhook-receiver
#
# For Objectif Libre usage, it's
# https://github.com/ObjectifLibre/gitlab-webhook-receiver
#
# For the systemd version with rsync, it's 
# https://github.com/sroutier/gitlab-webhook-receiver
#
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import argparse
import json
import logging
import logging.handlers
import os
import sys
import re
import shutil
import subprocess
import requests
import ssl
import urlparse

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

# Enabling debugging at http.client level (requests->urllib3->http.client)
# you will see the REQUEST, including HEADERS and DATA, and RESPONSE with
# HEADERS but without DATA.
# the only thing missing will be the response.body which is not logged.


CONFIG_FILE = "/etc/gitlab-webhook-receiver.conf"

arg_parser = argparse.ArgumentParser(description='Forward webhooks to '
                                     'the puppet Code Manager')
arg_parser.add_argument('--config', help='Path to the %(prog)s configuration',
                        default=CONFIG_FILE)
args = arg_parser.parse_args()

Config = configparser.ConfigParser()
Config.read(args.config)

log_level = logging.getLevelName(Config.get("general", "log_level")) or "DEBUG"
log_file = Config.get("general", 'log_file') or "/var/log/gitlab-webhook.log"

git_project = Config.get("general", 'git_project') or "ops"
git_target_dir = Config.get("general", 'git_target_dir') or "/tmp/git.target"
enable_rsync = Config.getboolean("general", 'enable_rsync')
rsync_target_dir = Config.get("general", 'rsync_target_dir') or "/tmp/rsync.target"
rsync_parms = Config.get("general", 'rsync_parms') or "-az --delete"


listen_port = Config.getint("general", "listen_port")
bind_address = Config.get("general", "bind_address")
enable_ssl = Config.getboolean("general", "enable_ssl")
if enable_ssl:
    keyfile = Config.get("general", 'keyfile')
    certfile = Config.get("general", 'certfile')

log_max_size = 25165824         # 24 MB

log = logging.getLogger('log')
log.setLevel(log_level)
log_handler = logging.handlers.RotatingFileHandler(log_file,
                                                   maxBytes=log_max_size,
                                                   backupCount=4)
f = logging.Formatter("%(asctime)s %(filename)s %(levelname)s %(message)s",
                      "%B %d %H:%M:%S")
log_handler.setFormatter(f)
log.addHandler(log_handler)

pid_file_name = Config.get("general", 'pid_file') or "/var/run/gitlab-webhook-receiver/gitlab-webhook.pid"
if os.access(pid_file_name, os.F_OK):
        log.warning("Previous PID file found, checking if process exits.")
        #if the lockfile is already there then check the PID number
        #in the lock file
        pidfile = open(pid_file_name, "r")
        pidfile.seek(0)
        old_pid = pidfile.readline()
        # Now we check the PID from lock file matches to the current
        # process PID
        if os.path.exists("/proc/%s" % old_pid):
                log.error("You already have an instance of the program running with pid: %s", old_pid)
                sys.exit(1)
        else:
                log.warning("Old process %s not found, removing old PID file.", old_pid)
                os.remove(pid_file_name)

# Create PID file for current process.
pidfile = open(pid_file_name, "w")
pidfile.write("%s" % os.getpid())
pidfile.close()


class webhookReceiver(BaseHTTPRequestHandler):

    def run_it(self, cmd):
        """
            runs a command
        """
        p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        log.debug('running:%s' % cmd)
        p.wait()
        if p.returncode != 0:
            log.critical("Non zero exit code:%s executing: %s" % (p.returncode,
                                                                  cmd))
        return p.stdout

    def git_cleanup(self):
        """
            cleans up the master, does a prune origin
        """
        log.debug('git_cleanup begins')
        os.chdir(git_target_dir)
        cmd = "git reset --hard HEAD"
        self.run_it(cmd)
        cmd = "git pull"
        self.run_it(cmd)
        cmd = "git remote prune origin"
        self.run_it(cmd)
        log.debug('git_cleanup ends')


    def rsync(self):
        """
            rsync to target area
        """
        log.debug('rsync begins')
        cmd = "rsync " + rsync_parms + " " + git_target_dir + " " + rsync_target_dir
        self.run_it(cmd)
        log.debug('rsync ends')


    def do_POST(self):
        """
            receives post, handles it
        """
        log.debug('got post')
        message = 'OK'
        self.rfile._sock.settimeout(5)
        data_string = self.rfile.read(int(self.headers['Content-Length']))
        self.send_response(200)
        self.send_header("Content-type", "text")
        self.send_header("Content-length", str(len(message)))
        self.end_headers()
        self.wfile.write(message)
        log.debug('gitlab connection should be closed now.')


        # parse data
        req_json = json.loads(data_string)
        req_text_pretty = json.dumps(req_json, indent=2)
        log.debug("Request json pretty dump: %s", req_text_pretty)
        req_project_name = req_json["project"]["name"]
        log.debug("REQ Project name: %s", req_project_name)
        if git_project == req_project_name:
            log.debug('project is in text')
            self.git_cleanup()
            if enable_rsync:
                self.rsync()
            log.debug('processing done.')
        else:
            log.debug('project name not in text, ignoring post')

    def log_message(self, formate, *args):
        """
            disable printing to stdout/stderr for every post
        """
        return


def main():
    """
        the main event.
    """
    try:
        server = HTTPServer((bind_address, listen_port), webhookReceiver)
        if enable_ssl:
            server.socket = ssl.wrap_socket(server.socket, keyfile=keyfile,
                                            certfile=certfile,
                                            server_side=True)
        log.info('started web server...')
        server.serve_forever()
    except KeyboardInterrupt:
        log.info('ctrl-c pressed, shutting down.')
        server.socket.close()
        os.remove(pid_file_name)

if __name__ == '__main__':
    main()


    
