#!/usr/bin/env python

from distutils.core import setup

setup(name='cmdgen',
      version='0.5.3',
      description='Simple command generator',
      keywords='generator cli',
      author='Victor Yarmola',
      author_email='std.feanor@gmail.com',
      url='https://github.com/stdk/cmdgen',
      install_requires=['ply>=3.10','jinja2'],
      packages=['cmdgen'],
      package_data={'cmdgen': ['templates/*']},
      scripts=['scripts/cmdgen'],
      classifiers=[
        'Topic :: Text Processing',
        'Environment :: Console',
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'License :: OSI Approved :: BSD License',
        'Topic :: Software Development :: Libraries :: Python Modules',
      ],
     )
