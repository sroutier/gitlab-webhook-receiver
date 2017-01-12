# Introduction

gitlab-webhook-receiver is a script to receive http posts from gitlab and then
pull the latest branches from a git repo. 
Optionally it can also replicate that pulled git repository to a 3rd location as a backup
or for any other testing purpuses.


# License

gitlab-webhook-receiver is released under the [GPL v2](http://www.gnu.org/licenses/gpl-2.0.html).


# Documentation

(1) Modify the config
---------------------

The configuration file `/etc/gitlab-webhook-receiver.conf` can be modified to suit your needs:
<pre>
[general]
log_level=WARNING
log_file = /var/log/gitlab-webhook-receiver/gitlab-webhook.log

bind_address = 0.0.0.0
listen_port = 8061

pid_file = /var/run/gitlab-webhook-receiver/gitlab-webhook.pid

git_project = TestProject01
git_target_dir = /home/test_user/projects/test/TestProject01

enable_rsync = true
rsync_target_dir = /home/other_user/projects
rsync_parms = -az --delete

# enable_ssl : listen_port is HTTPS
enable_ssl = False

# keyfile : path to the SSL key for listen_poprt
keyfile = "/etc/ssl/private_keys/localhost.pem"

# certfile : path to the SSL cert for listen_poprt
certfile = "/etc/ssl/certs/localhost.cert"
</pre>

update it with where your dirs live.


(2) create the gitlab webhook
-----------------------------

In gitlab, as admin, go to "Hooks" tab, create hook as:
http://your.ip.goes.here:8000

or change the port on line 175 of the script.


(3) Do initial checkout manually
--------------------------------
Whatever your git_dir is, do the first checkout manually. The script is made
to work with a pre-existing setup; and this gives you a chance to make sure
your permissions/ssh keys are all setup properly. 


# Trouble getting it working?

Let me know what's happening and I'll try to help. Email me at
sroutier@gmail.com.


# Contributing

We are open to any feedback / patches / suggestions.

2012 Shawn Sterling <shawn@systemtemplar.org>
2016 Guillaume Espanel <guillaume.espanel@objectif-libre.com>
2017 Sebastien Routier <sroutier@gmail.com>
