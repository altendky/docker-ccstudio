import pathlib
import re
import subprocess
import sys

paths = set()
packages = set()

for line in sys.stdin:
    if line.startswith('open'):
        if 'no such file' in line.casefold():
            continue

        p, = re.finditer('"([^"]+)"', line)
        path = p[1]

        if path in paths:
            continue
        if path.startswith(('/opt/ti/', '/home/')) or not path.startswith('/'):
            continue

        paths.add(path)

        package = subprocess.run(
            [
                'dpkg',
                '-S', p[1],
            ],
            stdout=subprocess.PIPE,
            encoding='UTF-8',
        ).stdout
        if len(package) > 100:
            print('ack', p[1])
            break
        package, _, _ = package.rpartition(':')
        packages.add(package)

print(' '.join(sorted(packages)))
