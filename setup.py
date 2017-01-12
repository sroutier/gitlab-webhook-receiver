try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'gitlab-webhook-receiver receives webhooks requests'
    'from git lab and sends them to Puppet',
    'author': 'Shawn Sterling Guillaume Espanel Sebastien Routier',
    'url': 'https://github.com/sroutier/gitlab-webhook-receiver',
    'author_email': 'shawn@systemtemplar.org, '
                    'guillaume.espanel@objectif-libre.com, '
                    'sroutier@gmail.com',
    'version': '1.0',
    'install_requires': ['requests'],
    'packages': ['gitlab_webhook_receiver'],
    'entry_points': {'console_scripts':
                     ['gitlab-webhook-receiver=gitlab_webhook_receiver.gitlab_webhook_receiver:main']
                     },
    'name': 'gitlab-webhook-receiver',
    'data_files': [('/etc', ['etc/gitlab-webhook-receiver.conf']),
                   ('/lib/systemd', ['lib/systemd/gitlab-webhook-receiver.service']),
                   ]
}

setup(**config)

