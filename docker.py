#!/usr/bin/env python3

import os
import pathlib
import re
import shutil
import subprocess
import sys
import tarfile
import time

import psutil


class ProcessNotFoundError(Exception):
    pass


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

    for parent in reversed(pathlib.Path(setup).parents):
        print(list(parent.iterdir()))

    try:
        print('setup:', setup)
        subprocess.run(
            [
                setup,
                '--mode', 'unattended',
                # '--unattendedmodeui', 'none',
                '--prefix', os.fspath(prefix),
                '--response-file', install/'ccstudio_installation_responses',
            ],
            check=True
        )
        print('succcesss--------------------------------')
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

    ccstudio = installed/'eclipse'/'ccstudio'

    for parent in reversed(ccstudio.parents):
        print(list(parent.iterdir()))

    link = pathlib.Path(os.sep)/'usr'/'local'/'bin'/'ccstudio'
    link.symlink_to(ccstudio)

    iu = os.environ.get('IU', '')
    if len(iu) > 0:
        print('Installing IU {}'.format(iu))
        install_iu(iu=iu, ccstudio=ccstudio)
    else:
        print('No IU specified for installation')

    shutil.rmtree(install)


def install_iu(iu, ccstudio):
    xvfb_command = [
        'Xvfb',
        ':0',
        '-screen', '0',
        '1024x768x16',
    ]

    x11vnc_command = [
        'x11vnc',
        '-display', ':0',
    ]

    install_iu_command = [
        os.fspath(ccstudio),
        '-noSplash',
        '-application',
        'org.eclipse.equinox.p2.director',
        '-repository', (
            'http://software-dl.ti.com'
            '/dsps/dsps_public_sw/sdo_ccstudio/codegen/Updates/p2linux/'
            ),
        '-installIUs', iu,
    ]

    post_install_command = [
        os.fspath(ccstudio),
        '-noSplash',
        '-application', 'com.ti.ccstudio.apps.projectBuild',
        '-help',
    ]

    subprocess.Popen(xvfb_command)
    subprocess.Popen(x11vnc_command)
    subprocess.run(install_iu_command, check=True)

    display_environment = {
        **os.environ,
        'DISPLAY': ':0',
    }

    subprocess.run(post_install_command, check=True, env=display_environment)

    pattern = '^ccs_update'

    process = None
    while process is None:
        try:
            process = get_process(pattern)
        except ProcessNotFoundError:
            time.sleep(0.1)
            continue

    print(process)
    before = time.monotonic()
    print(before)
    process.wait()
    after = time.monotonic()
    print(after)
    print('delta:', after - before)


def get_process(pattern):
    for process in psutil.process_iter():
        if re.search(pattern, process.name()):
            return process

    raise ProcessNotFoundError(
        'Pattern {!r} not found in process names'.format(pattern),
    )


if __name__ == '__main__':
    sys.exit(main())
