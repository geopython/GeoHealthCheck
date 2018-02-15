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

from email.mime.text import MIMEText
import email.utils
import logging
import smtplib

from flask_babel import gettext
from util import render_template2

LOGGER = logging.getLogger(__name__)


def notify(config, resource, run, last_run_success):
    """execute a notification"""

    status_changed = False

    this_run_success = run.success

    if last_run_success and not this_run_success:
        result = gettext('Failing')
    elif not last_run_success and this_run_success:
        result = gettext('Fixed')
    elif not last_run_success and not this_run_success:
        result = gettext('Still Failing')
    elif last_run_success and this_run_success:
        result = gettext('Passing')

    if result != gettext('Passing'):
        status_changed = True

    # Check if still 'Still Failing' result should be notified
    if result == gettext('Still Failing') \
            and not config['GHC_NOTIFICATIONS_VERBOSITY']:
        # Receive just 'Failing' and 'Fixed' notifications
        status_changed = False

    if not status_changed:
        return

    print('Notifying: status changed: result=%s' % result)

    template_vars = {
        'result': result,
        'config': config,
        'resource': resource,
        'run': run
    }

    msgbody = render_template2('notification_email.txt', template_vars)

    msg = MIMEText(msgbody)

    msg['From'] = email.utils.formataddr((config['GHC_SITE_TITLE'],
                                          config['GHC_ADMIN_EMAIL']))

    notifications_email = ','.join(resource.get_recipients('email'))
    if not notifications_email:
        LOGGER.warning("No emails for notification set for resource %s",
                       resource.identifier)
        return

    msg['To'] = notifications_email

    msg['Subject'] = '[%s] %s: %s' % (config['GHC_SITE_TITLE'],
                                      result, resource.title)

    print(msg.as_string())
    server = smtplib.SMTP(config['GHC_SMTP']['server'],
                          config['GHC_SMTP']['port'])

    if config['DEBUG']:
        server.set_debuglevel(True)

    if config['GHC_SMTP']['tls']:
        server.starttls()
        server.login(config['GHC_SMTP']['username'],
                     config['GHC_SMTP']['password'])
    try:
        server.sendmail(config['GHC_ADMIN_EMAIL'],
                        config['GHC_NOTIFICATIONS_EMAIL'],
                        msg.as_string())
    except Exception as err:
        LOGGER.exception(str(err))
    finally:
        server.quit()

    return True
