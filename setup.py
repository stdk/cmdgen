#!/usr/bin/env python

from distutils.core import setup

setup(name='cmdgen',
      version='0.5',
      description='Simple command generator',
      keywords='generator cli',
      author='Victor Yarmola',
      author_email='std.feanor@gmail.com',
      url='https://github.com/stdk/cmdgen',
      install_requires=['ply>=3.10','jinja2'],
      packages=['cmdgen'],
      scripts=['scripts/cmdgen'],
      classifiers=[
        'Environment :: Console',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'License :: BSD License',
        'Topic :: Software Development :: Libraries :: Python Modules',
      ],
     )
