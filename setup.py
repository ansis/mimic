#!/usr/bin/env python

from setuptools import setup


setup(
    name='Mimic',
    version='0.1.0',
    description="Tool for making remote directories mimic local file changes.",
    author='Ansis Brammanis',
    author_email='ansis.brammanis@gmail.com',
    license='BSD',
    url='https://github.com/ansis/mimic',
    download_url='https://github.com/ansis/mimic/tarball/master',
    packages=['mimic'],
    install_requires=(
        'pyinotify',
        'Pyro'
    ),
    entry_points={
        'console_scripts': [
            'mimic = mimic.main:main'
        ]
    },
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Operating System :: POSIX :: Linux'
    )
)

