# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#
# Copyright (c) 2014 Tom Kralidis
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# =================================================================

import logging
import smtplib

import jinja2

LOGGER = logging.getLogger(__name__)


def notify(config, resource, run):
    """execute a notification"""

    status_changed = False

    last_run_success = resource.last_run.success
    this_run_success = run.success

    if last_run_success and not this_run_success:
        result = 'Failing'
    elif not last_run_success and this_run_success:
        result = 'Fixed'
    elif not last_run_success and not this_run_success:
        result = 'Still Failing'
    elif last_run_success and this_run_success:
        result = 'Passing'

    if result != 'Passing':
        status_changed = True

    if not status_changed:
        return

    template_loader = jinja2.FileSystemLoader('GeoHealthCheck/templates')
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template('notification_email.txt')

    fromaddr = '%s <%s>' % (config['GHC_SITE_TITLE'],
                            config['GHC_ADMIN_EMAIL'])
    toaddrs = config['GHC_ADMIN_EMAIL']

    template_vars = {
        'result': result,
        'config': config,
        'resource': resource,
        'run': run
    }

    msg = template.render(template_vars)

    server = smtplib.SMTP('%s:%s' % (config['GHC_SMTP']['server'],
                                     config['GHC_SMTP']['port']))

    if config['GHC_SMTP']['tls']:
        server.starttls()
        server.login(config['GHC_SMTP']['username'],
                     config['GHC_SMTP']['password'])
    server.sendmail(fromaddr, toaddrs, msg)
    server.quit()

    return True
