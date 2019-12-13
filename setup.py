import io
import os
from setuptools import find_packages, setup

def read(filename, encoding='utf-8'):
    """read file contents"""
    full_path = os.path.join(os.path.dirname(__file__), filename)
    with io.open(full_path, encoding=encoding) as fh:
        contents = fh.read().strip()
    return contents

def get_package_version():
    """get version from top-level package init"""
    version_file = read('VERSION')
    if version_file:
        return version_file
    raise RuntimeError("Unable to find version string.")

setup(
    name='geohealthcheck',
    version=get_package_version(),
    license='MIT',
    install_requires=read('requirements.txt').splitlines(),
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'geohc=ghc_cli:cli',
        ]
    }
)
