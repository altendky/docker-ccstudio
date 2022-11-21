#!/usr/bin/env python3

import contextlib
import functools
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tarfile
import time
import typing

import attr
import click
import psutil


class ProcessNotFoundError(Exception):
    pass


print_flush = functools.partial(print, flush=True)


@attr.frozen
class Iu:
    name: str
    version: typing.Tuple[str]

    @classmethod
    def from_string(cls, s):
        name, version_string = s.split('/')
        version = tuple(segment for segment in version_string.split('.'))

        return cls(name=name, version=version)

    def with_imprecise_version(self, n):
        return attr.evolve(self, version=self.version[:n])

    def approximately_equal(self, other, n):
        return self.with_imprecise_version(n=n) == other.with_imprecise_version(n=n)

    def conflicts(self, others, n=2):
        """IUs conflict if they are not equal but are approximately equal."""
        for other in others:
            if other == self:
                continue
            if self.approximately_equal(other, n=n):
                return True

        return False

    def __str__(self):
        version_string = '.'.join(segment for segment in self.version)
        return f'{self.name}/{version_string}'


@click.command()
@click.option('--tarball', required=True, type=click.Path(dir_okay=False, exists=True))
@click.option('--install-iu', 'install_ius', envvar='INSTALL_IUS', multiple=True)
@click.option('--uninstall-iu', 'uninstall_ius', envvar='UNINSTALL_IUS', multiple=True)
def main(tarball, install_ius, uninstall_ius):
    requested_install_ius = {Iu.from_string(iu) for iu in install_ius}
    requested_uninstall_ius = {Iu.from_string(iu) for iu in uninstall_ius}

    tarball_path = pathlib.Path(tarball)
    install = pathlib.Path(os.getcwd())

    installer = install / 'installer'
    installer.mkdir(exist_ok=True)

    with tarfile.open(tarball_path.name) as tarball:
        base, = {
            pathlib.Path(member.name).parts[0]
            for member in tarball.getmembers()
        }
        def is_within_directory(directory, target):
            
            abs_directory = os.path.abspath(directory)
            abs_target = os.path.abspath(target)
        
            prefix = os.path.commonprefix([abs_directory, abs_target])
            
            return prefix == abs_directory
        
        def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
        
            for member in tar.getmembers():
                member_path = os.path.join(path, member.name)
                if not is_within_directory(path, member_path):
                    raise Exception("Attempted Path Traversal in Tar File")
        
            tar.extractall(path, members, numeric_owner=numeric_owner) 
            
        
        safe_extract(tarball, path=installer)

    setup, = (installer/base).glob('ccs_setup_*.bin')

    prefix = pathlib.Path(os.sep)/'opt'/'ti'

    installed = prefix/'ccs'

    for parent in reversed(pathlib.Path(setup).parents):
        print_flush(list(parent.iterdir()))

    with virtual_display():
        try:
            print_flush('setup:', setup)
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
            print_flush('success--------------------------------')
        except subprocess.CalledProcessError:
            install_logs = installed/'install_logs'
            for parent in install_logs.parents:
                print_flush('checking: ', parent, parent.exists())
            install_logs = list(path for path in install_logs.rglob('*') if path.is_file())
            print_flush('potential install logs:')
            for install_log in install_logs:
                print_flush('    --------: {}'.format(install_log))
                with open(install_log) as f:
                    for line in f:
                        sys.stdout.write(line)

            raise

        ccstudio = installed/'eclipse'/'ccstudio'

        for parent in reversed(ccstudio.parents):
            print_flush(list(parent.iterdir()))

        link = pathlib.Path(os.sep)/'usr'/'local'/'bin'/'ccstudio'
        link.symlink_to(ccstudio)

        installed_ius = get_installed_ius(ccstudio=ccstudio)
        ius_to_install = requested_install_ius - installed_ius

        # We need to uninstall IUs that are not equal to install request but
        # are approximately equal to them.  While I have successfully
        # installed, for example, 18.12.3 and 18.12.4 in the GUID, the CLI
        # installation mechanisms seem to dislike that.
        needed_uninstall_ius = {
            installed_iu
            for installed_iu in installed_ius
            if installed_iu.conflicts(others=requested_install_ius, n=2)
        }

        ius_to_uninstall = {*needed_uninstall_ius, *requested_uninstall_ius}

        print_flush('\n---- IUs present before:')
        for iu_to_uninstall in installed_ius:
            print_flush(f'    {iu_to_uninstall}')

        print_flush('\n---- IUs to uninstall:')
        for iu_to_uninstall in ius_to_uninstall:
            print_flush(f'    {iu_to_uninstall}')

        print_flush('\n---- IUs to install:')
        for iu_to_install in ius_to_install:
            print_flush(f'    {iu_to_install}')

        for iu_to_uninstall in ius_to_uninstall:
            uninstall_iu(ccstudio=ccstudio, iu=iu_to_uninstall)

        for needed_install_iu in ius_to_install:
            install_iu(ccstudio=ccstudio, iu=needed_install_iu)

    # TODO: seemed to take awhile then output nothing.
    # installed_ius = get_installed_ius(ccstudio=ccstudio)
    # print_flush('\n---- IUs present after:')
    # for iu_to_uninstall in installed_ius:
    #     print_flush(f'    {iu_to_uninstall}')

    shutil.rmtree(install)


def run_director(ccstudio, extras):
    command = [
        os.fspath(ccstudio),
        '-noSplash',
        '-application',
        'org.eclipse.equinox.p2.director',
        *extras,
    ]
    return subprocess.run(
        args=command,
        check=True,
        encoding='utf-8',
        stdout=subprocess.PIPE,
    )


def get_installed_ius(ccstudio):
    completed_process = run_director(ccstudio=ccstudio, extras=['-listInstalledRoots'])
    lines = completed_process.stdout.splitlines()

    return {
        Iu.from_string(line)
        for line in lines
        if not line.startswith('Operation completed')
    }


def install_iu(ccstudio, iu):
    extras = [
        '-repository', (
            'http://software-dl.ti.com'
            '/dsps/dsps_public_sw/sdo_ccstudio/codegen/Updates/p2linux/'
        ),
        '-installIUs',
        str(iu),
    ]
    process_iu(extras=extras, ccstudio=ccstudio)


def uninstall_iu(iu, ccstudio):
    extras = ['-uninstallIUs', iu]
    process_iu(ccstudio=ccstudio, extras=extras)


@contextlib.contextmanager
def virtual_display():
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

    xvfb_process = subprocess.Popen(xvfb_command)
    try:
        x11vnc_process = subprocess.Popen(x11vnc_command)
        try:
            yield
        finally:
            x11vnc_process.kill()
    finally:
        xvfb_process.kill()


def process_iu(ccstudio, extras):
    install_iu_command = [
        os.fspath(ccstudio),
        '-noSplash',
        '-application',
        'org.eclipse.equinox.p2.director',
        *(str(extra) for extra in extras)
    ]

    post_install_command = [
        os.fspath(ccstudio),
        '-noSplash',
        '-application', 'com.ti.ccstudio.apps.projectBuild',
        '-help',
    ]

    subprocess.run(install_iu_command, check=True)

    display_environment = {
        **os.environ,
        'DISPLAY': ':0',
    }

    subprocess.run(post_install_command, check=True, env=display_environment)

    # pattern = '^ccs_update'
    #
    # process = None
    # while process is None:
    #     try:
    #         process = get_process(pattern)
    #     except ProcessNotFoundError:
    #         time.sleep(0.1)
    #         continue
    #
    # print_flush(process)
    # before = time.monotonic()
    # print_flush(before)
    # process.wait()
    # after = time.monotonic()
    # print_flush(after)
    # print_flush('delta:', after - before)


def get_process(pattern):
    for process in psutil.process_iter():
        if re.search(pattern, process.name()):
            return process

    raise ProcessNotFoundError(
        'Pattern {!r} not found in process names'.format(pattern),
    )


sys.exit(main())
