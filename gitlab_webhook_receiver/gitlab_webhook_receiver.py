#!/usr/bin/python -tt
#
# Copyright (C) 2012 Shawn Sterling <shawn@systemtemplar.org>
#               2016 Guillaume Espanel <guillaume.espanel@objectif-libre.com>
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

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import argparse
import json
import logging
import logging.handlers
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
hook_url = Config.get("general", 'hook_url')

ssl_verify = Config.getboolean("general", "ssl_verify")
if Config.has_option("general", "ssl_ca_cert") and ssl_verify:
    ssl_verify = Config.get("general", "ssl_ca_cert")


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


class webhookReceiver(BaseHTTPRequestHandler):

    def get_token_from_request(self):
        token = urlparse.parse_qs(
            urlparse.urlparse(self.path).query
        ).get('token')[0]
        return token

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
        text = json.loads(data_string)
        text = json.dumps(text, indent=2)
        if git_project in text:
            log.debug('project is in text')
            token = self.get_token_from_request()
            headers = {"X-Authentication": token}
            # DO that thing
            result = requests.post(hook_url,
                                   json={"deploy-all": True},
                                   headers=headers, verify=ssl_verify)
            log.info("Requested redeployment result : %s" % result)
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

if __name__ == '__main__':
    main()
