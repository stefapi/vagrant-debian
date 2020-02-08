#!python

#   Copyright (c) 2019  Stephane Apiou
#
#   Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
#   following conditions are met:
#   1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following
#   disclaimer.
#   2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
#   following disclaimer in the documentation and/or other materials provided with the distribution.
#   THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
#   INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#   DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#   SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
#   WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
#   USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import argparse
import getpass
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
import urllib.request
from os import path
from pathlib import Path
from shutil import which
from urllib.error import ContentTooShortError

import pkg_resources
from jinja2 import Environment, FileSystemLoader, Template

version="1.0"

class external_tools:
    def __init__(self):

        self.username = getpass.getuser()
        if self.username == "root":
            self.sudo=False
        else:
            self.sudo = True
        if not which("apt"):
            print("apt could not be located.\nThis probably means that this script is not lauched on Debian/Ubuntu Linux.")
            exit(1)
        if not which("virtualbox"):
            if self.call_root("apt install virtualbox virtualbox-dkms") != 0:
                print('installation failed please package manually')
        if not which("vagrant"):
            if self.call_root("apt install vagrant") != 0:
                print('installation failed please package manually')
        if not which("genisoimage"):
            if self.call_root("apt install genisoimage") != 0:
                print('installation failed please package manually')

    def call_root(self, command):
        """
        Call an external program which may need privileges
        :param command:
        """
        if self.sudo:
            return subprocess.call(shlex.split("sudo "+command))
        else:
            return subprocess.call(shlex.split(command))

country= {
    'us': { 'keymap':'us', 'locale': 'en_US.UTF-8', 'timezone': 'US/Eastern'},
    'fr': {'keymap': 'fr(latin9)', 'locale': 'fr_FR.UTF-8', 'timezone': 'Europe/Paris'},
    'de': {'keymap': 'de', 'locale': 'de_DE.UTF-8', 'timezone': 'Europe/Berlin'},
}

def generate(args):
    external = external_tools()
    updates = False
    if args.url is None:
        if args.type == 'stable':
            args.url = 'https://cdimage.debian.org/cdimage/release/current/amd64/iso-cd/'
            updates = True
        if args.type == 'weekly':
            args.url = 'https://cdimage.debian.org/cdimage/weekly-builds/amd64/iso-cd/'
        if args.type == 'daily':
            args.url = 'https://cdimage.debian.org/cdimage/daily-builds/daily/current/amd64/iso-cd/'
        if args.type == 'oldstable':
            args.url = 'https://cdimage.debian.org/cdimage/archive/latest-oldstable/amd64/iso-cd/'
            updates = True
        if args.type == 'oldoldstable':
            args.url = 'https://cdimage.debian.org/cdimage/archive/latest-oldoldstable/amd64/iso-cd/'
            updates = True
    if args.iso is None:
        file=None
        page = urllib.request.urlopen(args.url)
        for line in page:
            m=re.search('^.*(debian-[^em].*-netinst.iso).*$', str(line))
            if m is not None:
                file = m.group(1)
                break
        if file is None:
            print("Seems strange: no iso file to download found")
            exit(1)
        if not path.exists(file):
            print("Downloading "+ file)
            try:
                urllib.request.urlretrieve(args.url+file, "temp.iso")
            except ContentTooShortError:
                urllib.request.urlcleanup()
                print("Unable to download the file... aborting")
                exit(1)
            if os.path.exists(file): os.remove(file)
            os.rename("temp.iso", file)
    else:
        file = args.iso
    if not os.path.exists(file):
        print("File "+ file + "does not exist. Aborting")
        exit(1)
    if os.path.exists("iso_image"):
        external.call_root("bash -c 'umount iso_image >/dev/null 2>&1'")
        shutil.rmtree("iso_image", True)
    os.mkdir("iso_image")
    external.call_root("bash -c 'mount -t iso9660 -o loop "+file+" iso_image >/dev/null 2>&1'")
    if os.path.exists("dest_image"):
        shutil.rmtree("dest_image", True)
    os.mkdir("dest_image")
    subprocess.call(shlex.split("rsync -a -H -exclude=TRANS.TBL iso_image/ dest_image"))
    external.call_root("bash -c 'umount iso_image >/dev/null 2>&1'")
    shutil.rmtree("iso_image", True)
    subprocess.call(shlex.split("chmod -R u+w dest_image"))
    for filename in os.listdir("dest_image/isolinux"):
        if filename.endswith(".cfg"):
            fullname = "dest_image/isolinux/"+filename
            with open("output", 'w') as out:
                for line in open(fullname,'r'):
                    m = re.search('^timeout .*$', str(line))
                    if m is not None:
                        out.write("timeout 10\n")
                    else:
                        out.write(line)
            os.rename("output", fullname)
    template_dict = country[args.country]
    template_dict['root_passwd'] = args.root_pass
    template_dict['user_name'] = args.user
    template_dict['user_fullname'] = args.user_name
    template_dict['user_passwd'] = args.user_pass
    template_dict['hostname'] = args.hostname
    template_dict['updates'] = updates
    file_loader = FileSystemLoader(template_path)
    env = Environment(loader=file_loader)
    template = env.get_template('preseed.cfg')
    output = template.render(data=template_dict)
    with open("dest_image/preseed.cfg","w") as output_file:
        output_file.write(output)
    shutil.copy(template_path+"/isolinux.cfg", "dest_image/isolinux/txt.cfg")
    subprocess.call(shlex.split("vboxmanage controlvm Debian poweroff"))
    time.sleep(2)
    subprocess.call(shlex.split("vboxmanage unregistervm --delete Debian"))
    time.sleep(2)
    os.chdir("dest_image")
    subprocess.call(shlex.split("bash -c 'md5sum `find -follow -type f` > md5sum.txt'"))
    external.call_root("genisoimage -o ../"+args.out_iso+" -r -J -no-emul-boot -boot-load-size 4 -boot-info-table -b isolinux/isolinux.bin -c isolinux/boot.cat .")
    os.chdir("..")
    shutil.rmtree("dest_image", True)
    if external.username != "root":
        external.call_root("chown " + external.username + ":" + external.username + " " + args.out_iso)

    if os.path.exists("debian_disk.vmdk"): os.remove("debian_disk.vmdk")
    subprocess.call(shlex.split("vboxmanage import "+template_path+"/debian_vm.ovf"))
    subprocess.call(shlex.split("vboxmanage storageattach Debian --storagectl IDE --port 1 --device 0 --type dvddrive --medium "+args.out_iso))
    subprocess.call(shlex.split("vboxmanage createmedium disk --filename debian_disk.vmdk --size 40000 --variant standard"))
    subprocess.call(shlex.split("vboxmanage storageattach Debian --storagectl SATA --port 0 --device 0 --type hdd  --medium debian_disk.vmdk"))
    if args.headless:
        subprocess.call(shlex.split("vboxmanage startvm Debian --type headless"))
    else:
        subprocess.call(shlex.split("vboxmanage startvm Debian"))
    print("Wait until debian installation from DVD is completed")
    iterate = True
    while iterate:
        time.sleep(10)
        proc = subprocess.Popen(shlex.split("vboxmanage showvminfo Debian --machinereadable"), stdout=subprocess.PIPE)
        out, err = proc.communicate()
        exitcode = proc.returncode
        m = re.search('VMState="running"', str(out))
        if m is None:
            iterate = False
    if os.path.exists("debian_temp.box"): os.remove("debian_temp.box")
    subprocess.call(shlex.split("vagrant package --base Debian --output debian_temp.box"))
    subprocess.call(shlex.split("vboxmanage unregistervm --delete Debian"))
    subprocess.call(shlex.split("vagrant box add --force --name Debian_temp debian_temp.box"))
    subprocess.call(shlex.split("vagrant destroy -f"))
    subprocess.call(shlex.split("vagrant up"))
    if os.path.exists(args.output): os.remove(args.output)
    subprocess.call(shlex.split("vagrant package --output "+ args.output))
    subprocess.call(shlex.split("vagrant destroy -f"))
    subprocess.call(shlex.split("vagrant box remove -f Debian_temp"))
    if os.path.exists("debian_temp.box"): os.remove("debian_temp.box")
    if args.add != None:
        subprocess.call(shlex.split("vagrant box add --force --name "+args.add+" "+args.output))
        if args.clean:
            cleanup_type(args, 'allbut')
    else:
        if args.clean:
            cleanup_type(args, 'clean')
    return 0

def cleanup(args):
    if args.clean:
        cleanup_type(args,'clean')
    if args.generated:
        cleanup_type(args,'generated')
    if args.all:
        cleanup_type(args, 'all')
    return 0

def cleanup_type(args, style):
    action_list = []
    if style == 'clean':
        action_list.append("debianiso")
        action_list.append("mydebian")
    if style == 'generated':
        action_list.append("mydebian")
    if style == 'allbut':
        action_list.append("debianiso")
        action_list.append("mydebian")
        action_list.append("box")
    if style == 'all':
        action_list.append("debianiso")
        action_list.append("mydebian")
        action_list.append("box")
        action_list.append("vagrant")
    for item in action_list:
        if item == "debianiso":
            for p in Path(".").glob("debian-*.iso"):
                p.unlink()
        if item == "mydebian":
            try:
                os.remove(args.out_iso)
            except FileNotFoundError:
                pass
        if item == "box":
            for p in Path(".").glob(args.output):
                p.unlink()
        if item == "vagrant":
            subprocess.call(shlex.split( "vagrant box remove --force --all debian"))
    return 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="generate Vagrant box from Debian iso file")
    parser.add_argument('-v', '--version', help='Print version and exit', action='store_true')
    parser.add_argument('-i', '--out-iso', help='use this name for the output ISO file', nargs='?', default='debian_autoinstall.iso')
    parser.add_argument('-o', '--output', help='use this name as output box name', nargs='?', default='debian.box')
    subparsers = parser.add_subparsers(title='subcommands', description = 'Valid Subcommands',help = 'get help with --help', dest='command')
    build = subparsers.add_parser('create', help='create box file automatically from debian iso file')
    remove = subparsers.add_parser('cleanup', help='cleanup directory and remove all generated files')
    vagrant = subparsers.add_parser('vagrant', help='cleanup directory and remove all generated files')
    remove.add_argument('-a', '--all', help='remove everything including vagrant box in repository', action='store_true')
    remove.add_argument('-g', '--generated', help='remove all generated files', action='store_true')
    remove.add_argument('-c', '--clean', help='remove everything but vagrant box', action='store_true')
    remove.add_argument('-n', '--name', help='Name of vagrant box to remove ', nargs='?', default="Debian")
    build.add_argument('-H', '--headless', help='run debian installation in VM without display', action='store_true')
    build.add_argument('-t', '--type', help='Type of debian ISO to download: daily, weekly, stable, oldstable, oldoldstable', nargs='?', default='stable')
    build.add_argument('-d', '--url', help='URL of debian directory to download from', nargs='?')
    build.add_argument('-I', '--iso', help='use this ISO file instead of downloading', nargs='?')
    build.add_argument('-a', '--add', help='add the box file generated to vagrant repository', nargs='?', const='Debian')
    build.add_argument('-c', '--country', help='configure for this country', nargs='?', default='us')
    build.add_argument('-C', '--clean', help='keep only box file', action='store_true')
    build.add_argument('-P', '--root-pass', help='configure root password', nargs='?', default='vagrant')
    build.add_argument('-u', '--user', help='configure user login', nargs='?', default='vagrant')
    build.add_argument('-U', '--user-name', help='configure user name', nargs='?', default='vagrant')
    build.add_argument('-p', '--user-pass', help='configure user password', nargs='?', default='vagrant')
    build.add_argument('-m', '--hostname', help='configure hostname', nargs='?', default='debianhost')
    vagrant.add_argument('-d', '--debian-temp', help='use this ISO file instead of downloading', nargs='?', default='debian_temp.box')
    try:
        template_path = pkg_resources.resource_filename('vagrant_debian','templates/')
    except ModuleNotFoundError:
        template_path = 'templates'
    print (template_path)
    res = parser.parse_args(sys.argv[1:])
    if res.version:
        print( sys.argv[0]+" version "+ version)
        exit(0)
    if res.command is None:
        res.command="create"
        res.url = None
        res.iso = None
        res.type = 'stable'
        res.headless = False
        res.country = 'us'
        res.root_pass = 'vagrant'
        res.user = 'vagrant'
        res.user_name = 'vagrant'
        res.user_pass = 'vagrant'
        res.hostname = 'debianhost'
        res.debian_temp = 'debian_temp.box'
        res.add = 'Debian'
        res.clean = False
    if res.command == "create":
        exit(generate(res))
    if res.command == "cleanup":
        exit(cleanup(res))
    exit(1)

