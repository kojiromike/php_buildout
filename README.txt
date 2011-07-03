This buildout runs a whole PHP development environment from a single directory.

Installation
------------

$ python bootstrap.py 
Downloading http://pypi.python.org/packages/2.7/s/setuptools/setuptools-0.6c11-py2.7.egg
Installing 'setuptools', 'zc.buildout'.
We have the best distribution that satisfies 'setuptools'.
Picked: setuptools = 0.6c12dev-r88846
We have the best distribution that satisfies 'zc.buildout'.
Picked: zc.buildout = 1.5.2

$ bin/buildout

[ now wait a little while ]

$ bin/supervisord

[now you can access the supervisor via the browser: http://localhost:9090]