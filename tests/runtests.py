#!/usr/bin/env python
import os
import sys
from os.path import abspath, dirname, join as pjoin

import django
from django.conf import settings


def runtests(verbosity=1, interactive=True, failfast=True,
             settings_module='settings.default'):
    here = abspath(dirname(__file__))
    root = pjoin(here, os.pardir)

    sys.path[0:0] = [here, root, pjoin(root, 'sorl')]
    os.environ['DJANGO_SETTINGS_MODULE'] = settings_module

    if django.VERSION >= (1, 7):
        django.setup()

    from django.test.utils import get_runner

    sys.stdout.write("Running tests for '%s' \n" % settings_module)

    TestRunner = get_runner(settings)

    test_runner = TestRunner(
        verbosity=verbosity,
        interactive=interactive,
        failfast=failfast
    )

    return test_runner.run_tests(settings.INSTALLED_APPS)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Runs the test suite for sorl-thumbnail.'
    )

    parser.add_argument(
        '--settings',
        dest='settings_module',
        action='store',
        default='settings.default',
        help='Specify settings module.')

    parser.add_argument(
        '--noinput',
        dest='interactive',
        action='store_false',
        default=True,
        help='Do not prompt the user for input of any kind.')

    parser.add_argument(
        '--failfast',
        dest='failfast',
        action='store_true',
        default=True,
        help='Stop running the test suite after first failed test.')

    args = parser.parse_args()

    failures = runtests(
        verbosity=2,
        interactive=args.interactive,
        failfast=args.failfast,
        settings_module=args.settings_module
    )

    if failures:
        sys.exit(bool(failures))
