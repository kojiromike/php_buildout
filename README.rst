PHP Buildout environment
========================

This buildout runs a whole PHP development environment from a single directory.

Included Software

- Supervisor

- Apache HTTP Server 2.2.17

- PHP 5.3.6 with the following extensions and PEAR packages (newest version if not specified):

  - Memcached 1.0.2

  - APC

  - XDebug

  - PHPUnit

  - PHP_Depend

  - PHPCPD

  - PHP PMD

  - DbUnit

  - PHPUnit MockObject

  - PHPUnit Selenium

  - PHPDocumentor

- Memcached 1.4.5

- libmemcached 0.48

- MySQL 5.1.53

- PostgreSQL 9.0.4

- MongoDB 1.8.2

Dependencies
------------

The following dependencies are needed and not already bundled with OSX. You can install them by using homebrew for example:

- cmake

- gettext

- curl

- jpeg

- libmcrypt

- libevent

- syck

- readline

- pcre

- expat

- libiconv

- libgd

Installation
------------

Just check out the buildout package from github and run:

	python bootstrap.py 
	
	bin/buildout
	
Since all packages are compiled from source this process may take some time.

After that all services can be started with the built in supervisor:

	bin/supervisord

Now you can access the supervisor via the browser

	http://localhost:9090 
	
or via command line:

	bin/supervisorctl status
	
Apache HTTP server is reachable at

	http://localhost:8080
	
You can close all services and shut down the supervisor with

	bin/supervisorctl shutdown
	
Binaries of all services are symlinked to
	
	bin/
	