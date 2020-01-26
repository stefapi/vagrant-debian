Vagrant-Debian is a program to create vagrant boxes from Debian repositories

In order to run, you need:
- a Debian linux system
- Virtualbox (if not install Vagrant-Debian will install it for you)
- Vagrant (Same, it's installed if not detected)

To run, just type on command line:
``` bash
vagrant-debian create --add --clean --headless
```

This will silently download the Debian media, lauch a virtualbox with the media, install the debian system, add mecessary packages and create a runnable and minimal vagrant box.

The size of result box is about 300MB large.

Please use:
``` bash
vagrant-debian --help
```
To display command help
or:
``` bash
vagrant-debian create --help
```
To display help on `create` subcommand.
