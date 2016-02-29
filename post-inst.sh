#! /bin/sh
useradd -r gitlab-webhook-receiver -d /var/lib/gitlab-webhook-receiver -m
mkdir -p /var/log/gitlab-webhook-receiver
chown gitlab-webhook-receiver: /var/log/gitlab-webhook-receiver
