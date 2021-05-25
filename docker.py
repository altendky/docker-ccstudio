#!/usr/bin/env python3

import os
import pathlib
import re
import shutil
import subprocess
import sys
import tarfile
import time

import click
import psutil


class ProcessNotFoundError(Exception):
    pass


@click.command()
@click.option('--tarball', required=True, type=click.Path(dir_okay=False, exists=True))
@click.option('--install-iu', 'install_ius', envvar='INSTALL_IUS', multiple=True)
@click.option('--uninstall-iu', 'uninstall_ius', envvar='UNINSTALL_IUS', multiple=True)
def main(tarball, install_ius, uninstall_ius):
    tarball_path = pathlib.Path(tarball)
    install = pathlib.Path(os.getcwd())

    installer = install / 'installer'
    installer.mkdir(exist_ok=True)

    with tarfile.open(tarball_path.name) as tarball:
        base, = {
            pathlib.Path(member.name).parts[0]
            for member in tarball.getmembers()
        }
        tarball.extractall(path=installer)

    setup, = (installer/base).glob('ccs_setup_*.bin')

    prefix = pathlib.Path(os.sep)/'opt'/'ti'

    installed = prefix/'ccs'

    for parent in reversed(pathlib.Path(setup).parents):
        print(list(parent.iterdir()))

    try:
        print('setup:', setup)
        subprocess.run(
            [
                setup,
                '--unattendedmodeui', 'none',
                '--mode', 'unattended',
                '--enable-components', 'PF_C28',
                '--prefix', os.fspath(prefix),
            ],
            check=True
        )
        print('success--------------------------------')
    except subprocess.CalledProcessError:
        install_logs = installed/'install_logs'
        for parent in install_logs.parents:
            print('checking: ', parent, parent.exists())
        install_logs = list(
            path
            for path in install_logs.rglob('*')
            if path.is_file()
        )
        print('potential install logs:')
        for maybe in install_logs:
            print('   ', maybe)
        for install_log in install_logs:
            print('    --------: {}'.format(install_log))
            with open(install_log) as f:
                for line in f:
                    sys.stdout.write(line)

        raise

    ccstudio = installed/'eclipse'/'ccstudio'

    for parent in reversed(ccstudio.parents):
        print(list(parent.iterdir()))

    link = pathlib.Path(os.sep)/'usr'/'local'/'bin'/'ccstudio'
    link.symlink_to(ccstudio)

    if len(install_ius) == 0:
        print('No IU specified for installation')
    else:
        for iu_to_install in install_ius:
            print('Installing IU {}'.format(iu_to_install))
            install_iu(iu=iu_to_install, ccstudio=ccstudio)

    if len(uninstall_ius) == 0:
        print('No IU specified for uninstallation')
    else:
        for iu_to_uninstall in uninstall_ius:
            print('Uninstalling IU {}'.format(iu_to_uninstall))
            uninstall_iu(iu=iu_to_uninstall, ccstudio=ccstudio)

    shutil.rmtree(install)


def install_iu(iu, ccstudio):
    process_iu(iu=iu, ccstudio=ccstudio, command='-installIUs')


def uninstall_iu(iu, ccstudio):
    process_iu(iu=iu, ccstudio=ccstudio, command='-uninstallIUs')


def process_iu(iu, ccstudio, command):
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
        command, iu,
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


sys.exit(main())
