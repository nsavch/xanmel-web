from fabric.api import *


env.hosts = ['xon.teichisma.info']
env.user = 'root'
local_user = 'xanmel'
local_home = '/home/xanmel/xanmel'
app_path = '/home/xanmel/xanmel-web'
venv_path = '/home/xanmel/venvs/xanmel-web'


def update_app():
    with cd(app_path):
        sudo('git pull', user=local_user)


def install_requirements():
    with cd(app_path):
        sudo('HOME=%s %s/bin/pip install -r requirements.txt' % (local_home, venv_path), user=local_user)


def update_systemd():
    put('conf/xanmel-web.service', '/etc/systemd/system/')
    run('systemctl daemon-reload')


def update_nginx():
    put('conf/nginx-site.conf', '/etc/nginx/sites-enabled/80xon.teichisma.info.conf')
    run('systemctl restart nginx')


def restart_server():
    run('systemctl restart xanmel-web')


def deploy():
    update_app()
    install_requirements()
    restart_server()
