#! /bin/sh
test -d /var/log/gitlab-webhook-receiver && chown -R nobody: /var/log/gitlab-webhook-receiver
userdel gitlab-webhook-receiver
