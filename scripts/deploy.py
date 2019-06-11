import argparse
import configparser
import os
import subprocess

from git import Repo
import yaml

KOLLA_ANSIBLE_REPO = 'https://github.com/openstack/kolla-ansible.git'
WORK_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INVENTORY = 'kolla-ansible/ansible/inventory/'
DEFAULT_GLOBALS = 'kolla-ansible/etc/kolla/globals.yml'


def provision_deploy_node(conf):
    os.chdir(WORK_DIR)
    install_kolla_ansible()
    generate_inventory(conf)
    generate_conf(conf)
    bootstrap_server(conf)
    prechecks(conf)
    deploy(conf)


def install_kolla_ansible():
    Repo.clone_from(
        KOLLA_ANSIBLE_REPO,
        os.path.join(WORK_DIR, 'kolla-ansible'))
    subprocess.run(
        'pip3 install -r kolla-ansible/requirements.txt',
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


def generate_inventory(conf):
    if len(conf.compute_nodes) == 1 \
            and conf.controller_nodes[0] == conf.compute_nodes[0]:
        inventory_file = 'all-in-one'
    else:
        inventory_file = 'multinode'

    inventory_parser = configparser.ConfigParser(allow_no_value=True)
    inventory_parser.read(os.path.join(
        DEFAULT_INVENTORY, inventory_file))

    if inventory_file == 'multinode':
        for section in (
                'control', 'network', 'monitoring', 'compute', 'storage'):
            for name in inventory_parser[section]:
                inventory_parser.remove_option(section, name)

        for control_section in ('control', 'network', 'monitoring'):
            inventory_parser.set(control_section, conf.controller_nodes[0])

        for compute_node in conf.compute_nodes:
            inventory_parser.set('compute', compute_node)

        with open(os.path.join(WORK_DIR, inventory_file), 'w') as config_file:
            inventory_parser.write(config_file, space_around_delimiters=False)


def generate_conf(conf):
    with open('/etc/kolla/globals.yml', 'w') as global_file:
        yaml.dump(dict(conf.kolla_ansible_conf), global_file)

    subprocess.run(
        './kolla-ansible/tools/generate_passwords.py',
        shell=True,
        check=True
    )


def bootstrap_server(conf):
    subprocess.run(
        './kolla-ansible/tools/kolla-ansible -i %s bootstrap-servers' % conf.inventory_file,
        shell=True,
        check=True
    )


def prechecks(conf):
    subprocess.run(
        './kolla-ansible/tools/kolla-ansible -i %s prechecks' % conf.inventory_file,
        shell=True,
        check=True
    )


def deploy(conf):
    subprocess.run(
        './kolla-ansible/tools/kolla-ansible -i %s deploy' % conf.inventory_file,
        shell=True,
        check=True
    )
    subprocess.run(
        './kolla-ansible/tools/kolla-ansible -i %s post-deploy' % conf.inventory_file,
        shell=True,
        check=True
    )


class Config(object):

    def __init__(self, config_file):
        self.config_file = config_file
        self.parser = configparser.ConfigParser(allow_no_value=True)
        self.compute_nodes, self.controller_nodes = [], []
        self.kolla_ansible_conf = None
        self.inventory_file = 'all-in-one'
        self.parse_config()

    def parse_config(self):
        self.parser.read(self.config_file)
        self.compute_nodes.extend(list(self.parser['compute'].keys()))
        self.controller_nodes.extend(list(self.parser['controller'].keys()))
        self.kolla_ansible_conf = self.parser['kolla-ansible']
        if len(self.compute_nodes) == 1 \
                and self.controller_nodes[0] == self.compute_nodes[0]:
            self.inventory_file = 'all-in-one'
        else:
            self.inventory_file = 'multinode'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='quickly setup kolla deployment')

    parser.add_argument('--config-file', dest='config_file', required=True,
                        help='path of config file with info of the deployment')

    args = parser.parse_args()
    provision_deploy_node(Config(args.config_file))
