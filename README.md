Vagrant-Debian is a program to create vagrant boxes from Debian repositories

In order to run, you need:
- a Debian linux system (maybe it works on Ubuntu)
- Virtualbox (if not install Vagrant-Debian will install it for you)
- Vagrant (Same, it's installed if not detected)
- a working -- and fast -- internet connection (about 500 MB will be downloaded)
- Enough diskspace on your current directory (around 3 Gbytes).
- Enough memory for your PC: 4Gbytes

To run, just type on command line:

        vagrant_debian create --add --clean --headless

This will silently download the Official Debian media, launch a virtualbox instance with the media, install the debian system, add necessary packages and create a runnable and minimal vagrant box.

The script is compatible with Jessie, Stretch, Bullseye and unstable Debian versions and maybe with older (not tested) or future ones. The version is choosen with a command line option.

Warning: with Buster, you have to install virtualbox by yourself as it's not part of standard Debian packages.

The size of created box is around 300MB large.

Please use:

        vagrant_debian --help

To display command help
or:

        vagrant_debian create --help

To display help on `create` subcommand.

Have fun !
