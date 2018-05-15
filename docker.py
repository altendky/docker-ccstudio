#!/usr/bin/env python3

import os
import pathlib
import re
import shutil
import subprocess
import sys
import tarfile


def main():
    install = pathlib.Path(os.getcwd())

    installer = install / 'installer'
    installer.mkdir(exist_ok=True)

    with tarfile.open(pathlib.Path(os.environ['TARBALL']).name) as tarball:
        base, = {
            pathlib.Path(member.name).parts[0]
            for member in tarball.getmembers()
        }
        tarball.extractall(path=installer)

    setup, = (installer/base).glob('ccs_setup_*.bin')
    major_version = int(re.match('.*_(\d+).*', setup.name)[1])

    prefix = pathlib.Path(os.sep)/'opt'/'ti'

    installed = prefix/'ccsv{}'.format(major_version)

    try:
        subprocess.run(
            [
                setup,
                '--mode', 'unattended',
                '--prefix', prefix,
                '--response-file', install/'ccstudio_installation_responses',
            ],
            check=True
        )
    except subprocess.CalledProcessError:
        install_logs = installed/'install_logs'
        for parent in install_logs.parents:
            print('checking: ', parent, parent.exists())
        install_logs, = install_logs.glob('*')
        install_log, = install_logs.glob('ccs_setup*_install.log')
        with open(install_log) as f:
            for line in f:
                sys.stdout.write(line)

        raise

    shutil.rmtree(install)

    ccstudio = installed/'eclipse'/'ccstudio'
    link = pathlib.Path(os.sep)/'usr'/'local'/'bin'/'ccstudio'
    link.symlink_to(ccstudio)


if __name__ == '__main__':
    sys.exit(main())
