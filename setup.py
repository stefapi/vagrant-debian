#!/usr/bin/env python
import os
import pathlib
import subprocess
import sys
import glob
import setuptools

PO_FILES = 'po/*/messages.po'

class CleanCommand(setuptools.Command):
    """
    Custom clean command to tidy up the project root, because even
        python setup.py clean --all
    doesn't remove build/dist and egg-info directories, which can and have caused
    install problems in the past.
    """
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        os.system('rm -vrf ./build ./dist ./*.pyc ./*.tgz ./*.egg-info')

if sys.version_info < (3, 6, 0):
    sys.exit("Python 3.6.0 is the minimum required version")

PROJECT_ROOT = os.path.dirname(__file__)

with open(os.path.join(PROJECT_ROOT, "README.md")) as file_:
    long_description = file_.read()

with open('vagrant_debian/__init__.py', 'rb') as fid:
    for line in fid:
        line = line.decode('utf-8')
        if line.startswith('__version__'):
            version = line.strip().split()[-1][1:-1]
            break

def create_mo_files():
    mo_files = []
    prefix = 'vagrant_debian'

    for po_path in glob.glob(str(pathlib.Path(prefix) / PO_FILES)):
        lang ='fr'
        mo_file = os.path.join(str(pathlib.Path(prefix)), 'mo', lang, 'LC_MESSAGES', prefix + '.mo')
        subprocess.run(['msgfmt', '-o', str(mo_file), po_path], check=True)
        mo_files.append(str(mo_file.relative_to(prefix)))
        mo_file_unix = (prefix.build_base + '/mo/' + lang +
                        '/LC_MESSAGES/gramps.mo')
        mo_dir = os.path.dirname(mo_file)
        if not(os.path.isdir(mo_dir) or os.path.islink(mo_dir)):
            os.makedirs(mo_dir)

        if os.path.getmtime(po_path) > os.path.getmtime(mo_file):
            cmd = 'msgfmt %s -o %s' % (po_path, mo_file)
            if os.system(cmd) != 0:
                os.remove(mo_file)
                msg = 'ERROR: Building language translation files failed.'
                ask = msg + '\n Continue building y/n [n] '
                reply = input(ask)
                if reply in ['n', 'N']:
                    raise SystemExit(msg)

        #linux specific piece:
        target = 'share/locale/' + lang + '/LC_MESSAGES'
        data_files.append((target, [mo_file_unix]))
    return mo_files

data_files = []
IMAGE_FILES = glob.glob(os.path.join('.', 'README.md'))
data_files.append(('share/vagrant_debian/', IMAGE_FILES))

package_data = []
package_data += create_mo_files()
package_data += ['templates/*']
setuptools.setup(
    name="vagrant_debian",
    version=version,
    python_requires=">=3.6.0",
    description="Create vagrant virtualbox from Debian ISO cd",
    long_description=long_description,
    long_description_content_type="text/markdown",
    platforms = ['Linux'],
    install_requires=[
        "jinja2",
        "wheel",
        "babel"
    ],
    url="https://github.com/apiou/vagrant-debian",
    author="Stephane APIOU",
    author_email="stephane@apiou.org",
    license="BSD-2",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: System :: Systems Administration",
        "Topic :: System :: Operating System",
        "Topic :: Utilities"
    ],
    message_extractors = {
        'vagrant_debian' : [
            ('**.py', 'python', None)
        ]
    },
    entry_points={
        'console_scripts': [
            'vagrant_debian = vagrant_debian.vagrant_debian:main'
        ]
    },
    packages=setuptools.find_packages(),
    data_files = data_files,
    include_package_data=True,
)

