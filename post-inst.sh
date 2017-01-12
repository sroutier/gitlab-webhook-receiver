#! /bin/sh
useradd --comment "GitLab WebHook" --groups wheel gl_webhook

mkdir -p /var/log/gitlab-webhook-receiver
chown gl_webhook: /var/log/gitlab-webhook-receiver

mkdir -p /var/run/gitlab-webhook-receiver
chown gl_webhook: /var/run/gitlab-webhook-receiver

cp /lib/systemd/gitlab-webhook-receiver.service /etc/systemd/system/gitlab-webhook-receiver.service
systemctl daemon-reload
