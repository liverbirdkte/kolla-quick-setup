import argparse
import configparser
import os
import subprocess

from git import Repo

KOLLA_ANSIBLE_REPO = 'https://github.com/openstack/kolla-ansible.git'
WORK_DIR = os.path.dirname(os.path.abspath(__file__))


def provision_deploy_node(controllers, computes):
    install_kolla_ansible()
    update_conf(controllers, computes)
    bootstrap_server()


def install_kolla_ansible():
    repo = Repo('kolla-ansible')
    repo.clone(KOLLA_ANSIBLE_REPO)
    subprocess.run(
        'sudo pip install -r kolla-ansible/requirements.txt',
        shell=True,
        check=True
    )
    subprocess.run('sudo mkdir -p /etc/kolla', shell=True, check=True)
    subprocess.run('sudo chown $USER:$USER /etc/kolla', shell=True, check=True)
    subprocess.run(
        'cp -r kolla-ansible/etc/kolla/* /etc/kolla',
        shell=True,
        check=True
    )
    subprocess.run(
        'cp kolla-ansible/ansible/inventory/* .',
        shell=True,
        check=True)


def update_conf(controllers, computes):
    if len(computes) == 1 \
            and controllers[0] == computes[0]:
        inventory_file = 'all-in-one'
    else:
        inventory_file = 'multinode'

    inventory_parser = configparser.ConfigParser(allow_no_value=True)
    inventory_parser.read(os.path.join(
        'kolla-ansible/ansible/inventory/', inventory_file))

    if inventory_file == 'multinode':
        for section in ('control', 'network', 'monitoring'):
            inventory_parser.remove_section(section)
            inventory_parser.add_section(section)
            inventory_parser.set(section, controllers[0])

        inventory_parser.remove_section('compute')
        inventory_parser.add_section('compute')
        for compute in computes:
            inventory_parser.set('compute', compute)

        inventory_parser.remove_option('storage', 'storage01')

    inventory_parser.write(os.path.join(WORK_DIR, inventory_file))


def bootstrap_server():
    pass


def prechecks():
    pass


def deploy():
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='quickly setup kolla deployment')

    parser.add_argument('--config-file', dest='config_file', required=True,
                        help='path of config file with info of the deployment')

    args = parser.parse_args()

    parser = configparser.ConfigParser(allow_no_value=True)
    parser.read(args.config_file)
    os.chdir(WORK_DIR)
    compute_nodes = list(parser['compute'].keys())
    controller_nodes = list(parser['controller'].keys())
    provision_deploy_node(controller_nodes, compute_nodes)
