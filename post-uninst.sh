#! /bin/sh
test -f /etc/systemd/system/gitlab-webhook-receiver.service && rm /etc/systemd/system/gitlab-webhook-receiver.service
test -d /var/run/gitlab-webhook-receiver && chown -R nobody: /var/run/gitlab-webhook-receiver
test -d /var/log/gitlab-webhook-receiver && chown -R nobody: /var/log/gitlab-webhook-receiver
userdel gl_webhook
