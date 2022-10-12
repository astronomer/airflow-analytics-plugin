# Copyright 2019 Astronomer Inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import re

from setuptools import Command, setup


def fpath(*parts):
    return os.path.join(os.path.dirname(__file__), *parts)


def read(*parts):
    return open(fpath(*parts)).read()


def desc():
    return read('README.md')


# https://packaging.python.org/guides/single-sourcing-package-version/
def find_version(*paths):
    version_file = read(*paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


# Cribbed from https://circleci.com/blog/continuously-deploying-python-packages-to-pypi-with-circleci/
class VerifyVersionCommand(Command):
    """Custom command to verify that the git tag matches our version"""
    description = 'verify that the git tag matches our version'
    user_options = []  # type: ignore

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        tag = os.getenv('CIRCLE_TAG')

        if tag != "v" + VERSION:
            info = "Git tag: {0} does not match the version of this app: v{1}".format(
                tag, VERSION
            )
            exit(info)

VERSION = "1.0.0"

setup(
    name='astronomer-analytics-plugin',
    version=VERSION,
    url='https://github.com/astronomer/airflow-analytics-plugin',
    license='Apache2',
    author='astronomerio',
    author_email='humans@astronomer.io',
    description='Analytics Plugin for Astronomer Platform',
    long_description=desc(),
    long_description_content_type='text/markdown',
    include_package_data=True,
    zip_safe=True,
    platforms='any',
    install_requires=[
        'apache-airflow>=1.10.0',
    ],
    setup_requires=[
        'pytest-runner~=4.0',
        'wheel',
    ],
    tests_require=[
        'astronomer-analytics-plugin[test]'
    ],
    extras_require={
        'test': [
            'flake8',
            'flake8-import-order>=0.18',
            'pytest',
            'pytest-flask',
            'pytest-mock',
            'pytest-cov',
        ]
    },
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3',
    ],
    cmdclass={"verify": VerifyVersionCommand},
    entry_points={
        "airflow.plugins": [
            "astronomer_analytics_plugin = astronomer_analytics_plugin.analytics_plugin:AstronomerPlugin"
        ]
    },
    packages=['astronomer_analytics_plugin'],
    package_dir={'astronomer_analytics_plugin': 'src/plugins'},
    package_data={'astronomer_analytics_plugin': ['templates/analytics_plugin/index.html']},
)
