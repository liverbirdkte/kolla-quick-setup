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
    bootstrap_server()


def install_kolla_ansible():
    repo = Repo.clone_from(
        KOLLA_ANSIBLE_REPO,
        os.path.join(WORK_DIR, 'kolla-ansible'))
    subprocess.check_call(
        'sudo pip install -r kolla-ansible/requirements.txt',
        shell=True
    )
    subprocess.check_call('sudo mkdir -p /etc/kolla', shell=True)
    subprocess.check_call('sudo chown $USER:$USER /etc/kolla', shell=True)
    subprocess.check_call(
        'cp -r kolla-ansible/etc/kolla/* /etc/kolla',
        shell=True)


def generate_inventory(conf):
    if len(conf.compute_nodes) == 1 \
            and conf.controller_nodes[0] == conf.compute_nodes[0]:
        inventory_file = 'all-in-one'
    else:
        inventory_file = 'multinode'

    print inventory_file
    inventory_parser = configparser.ConfigParser(allow_no_value=True)
    inventory_parser.read(os.path.join(
        DEFAULT_INVENTORY, inventory_file))

    if inventory_file == 'multinode':
        for section in (
                'control', 'network', 'monitoring', 'compute', 'storage'):
            for name, value in inventory_parser.items(section):
                inventory_parser.remove_option(section, name)

        for control_section in ('control', 'network', 'monitoring'):
            inventory_parser.set(control_section, conf.contrller_nodes[0])

        for compute_node in conf.compute_nodes:
            inventory_parser.set('compute', compute_node)

        with open(os.path.join(WORK_DIR, inventory_file), 'wb') as config_file:
            inventory_parser.write(config_file)


def generate_conf(conf):
    with open(DEFAULT_GLOBALS) as default_global_file:
        global_conf = yaml.load(
            default_global_file.read(), Loader=yaml.FullLoader)
    global_conf.update(conf.kolla_ansible_conf)
    with open('globals.yml', 'w') as new_global_file:
        yaml.dump(global_conf, new_global_file)

    subprocess.check_call('cp -f globals.yml /etc/kolla')


def bootstrap_server():
    pass


def prechecks():
    pass


def deploy():
    pass


class Config(object):

    def __init__(self, config_file):
        self.config_file = config_file
        self.parser = configparser.ConfigParser(allow_no_value=True)
        self.compute_nodes, self.controller.nodes = [], []
        self.kolla_ansible_conf = None
        self.parse_config()

    def parse_config(self):
        self.parser.read(self.config_file)
        self.compute_nodes.extend(list(parser['compute'].keys()))
        self.controller_nodes.extend(list(parser['controller'].keys()))
        self.kolla_ansible_conf = parser.items('kolla-ansible')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='quickly setup kolla deployment')

    parser.add_argument('--config-file', dest='config_file', required=True,
                        help='path of config file with info of the deployment')

    args = parser.parse_args()
    provision_deploy_node(Config(args.config_file))
