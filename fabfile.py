from fabric.api import *


env.hosts = ['xon.teichisma.info']
env.user = 'root'
local_user = 'xanmel'
app_path = '/home/xanmel/xanmel-web'
venv_path = '/home/xanmel/venvs/xanmel-web'


def update_app():
    with cd(app_path):
        sudo('git pull', user=local_user)


def install_requirements():
    with cd(app_path):
        sudo('%s/bin/pip install -r requirements.txt' % venv_path, user=local_user)


def restart_server():
    pass


def deploy():
    update_app()
    restart_server()
