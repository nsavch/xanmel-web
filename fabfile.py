from fabric.api import *


env.hosts = ['xon.teichisma.info']
env.user = 'root'
local_user = 'xanmel'
local_home = '/home/xanmel'
app_path = '/home/xanmel/xanmel-web'
venv_path = '/home/xanmel/venvs/xanmel-web'


def update_app():
    with cd(app_path):
        sudo('git pull', user=local_user)


def install_requirements():
    with cd(app_path):
        sudo('HOME=%s pipenv install' % (local_home, ), user=local_user)
    with cd('/home/xanmel/xanmel'):
        sudo('HOME=%s git pull' % local_home)


def update_systemd():
    put('conf/xanmel-web.service', '/etc/systemd/system/')
    run('systemctl daemon-reload')


def update_nginx():
    put('conf/nginx-site.conf', '/etc/nginx/sites-enabled/80xon.teichisma.info.conf')
    run('systemctl restart nginx')


def restart_server():
    run('systemctl restart xanmel-web')


def update_cron():
    put('conf/crontab', '/etc/cron.d/xanmel-web')
    run('chmod 644 /etc/cron.d/xanmel-web')


def deploy():
    update_app()
    install_requirements()
    restart_server()
