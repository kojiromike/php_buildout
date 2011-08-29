#!/usr/bin/env python
from setuptools import setup, find_packages

entry_points = """
[zc.buildout]
phpext = s2.recipe.phpext:PhpExt
"""

setup (
    name='s2.recipe',
    description = "Set of helper recipies for zc.buildout",
    version='0.1.0',
    author = "Tim Eggert",
    author_email = "tim@elbart.com",
    packages = find_packages(),
    include_package_data = True,
    namespace_packages = ['s2', 's2.recipe'],
    extras_require = dict(),
    install_requires = ['setuptools',
                        'hexagonit.recipe.download',
                        'zc.recipe.egg',
                        'py'
                        ],
    entry_points = entry_points,
    zip_safe = True,
    )
