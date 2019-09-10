#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
import types
import email.utils
import logging
import smtplib
import json

import requests
from flask_babel import gettext
from util import render_template2

LOGGER = logging.getLogger(__name__)


def do_email(config, resource, run, status_changed, result):
    # List of global email addresses to notify, may be list or
    # comma-separated str "To" needs comma-separated list,
    # while sendmail() requires list...

    if isinstance(config['GHC_NOTIFICATIONS_EMAIL'], types.StringTypes):
        config['GHC_NOTIFICATIONS_EMAIL'] = \
            config['GHC_NOTIFICATIONS_EMAIL'].split(',')

    # this should always be a list
    global_notifications = config['GHC_NOTIFICATIONS_EMAIL'] or []
    if not isinstance(global_notifications, (list, tuple, set,)):
        raise TypeError("Cannot use {} as list of emails".format(
                                       type(global_notifications)))

    notifications_email = global_notifications +\
        resource.get_recipients('email')

    if not notifications_email:
        LOGGER.warning("No emails for notification set for resource %s",
                       resource.identifier)
        return

    template_vars = {
        'result': result,
        'config': config,
        'resource': resource,
        'run': run
    }

    msgbody = render_template2('notification_email.txt', template_vars)
    msg = MIMEText(msgbody, 'plain', 'utf-8')
    msg['From'] = email.utils.formataddr((config['GHC_SITE_TITLE'],
                                          config['GHC_ADMIN_EMAIL']))
    msg['To'] = ','.join(notifications_email)
    msg['Subject'] = '[%s] %s: %s' % (config['GHC_SITE_TITLE'],
                                      result, resource.title)

    if not config.get('GHC_SMTP') or not\
        (any([config['GHC_SMTP'][k] for k in ('port',
                                              'server',
                                              'username',
                                              'password',)])):

        LOGGER.warning("No SMTP configuration. Not sending to %s",
                       notifications_email)
        print(msg.as_string())
        return

    server = smtplib.SMTP(config['GHC_SMTP']['server'],
                          config['GHC_SMTP']['port'])

    if config['DEBUG']:
        server.set_debuglevel(True)

    try:
        if config['GHC_SMTP']['tls']:
            server.starttls()
    except Exception as err:
        LOGGER.exception("Cannot connect to smtp: %s[:%s]: %s",
                         config['GHC_SMTP']['server'],
                         config['GHC_SMTP']['port'],
                         err,
                         exc_info=err)
        return
    try:
        server.login(config['GHC_SMTP']['username'],
                     config['GHC_SMTP']['password'])
    except Exception as err:
        LOGGER.exception("Cannot log in to smtp: %s", err,
                         exc_info=err)
    try:
        server.sendmail(config['GHC_ADMIN_EMAIL'],
                        notifications_email,
                        msg.as_string())
    except Exception as err:
        LOGGER.exception(str(err), exc_info=err)
    finally:
        server.quit()


def _parse_line(_line):
    try:
        k, v = _line.split('=', 1)
        return {k: v}
    except (IndexError, ValueError,):
        raise ValueError("Invalid line: {}".format(_line))


def _parse_webhook_location(value):
    """
    Parse Recipient.location and returns tuple of url and params

    location should be in form

    URL

    PAYLOAD

    where PAYLOAD is a list of fields and values in form

    FIELD_NAME=FIELD_VALUE

    alternatively, it can be dictionary serialized as json
    """
    if not value.strip():
        raise ValueError("No payload")
    value = value.strip()
    url = None
    params = {}
    lines = value.splitlines()

    for idx, line in enumerate(lines):
        if idx == 0:
            url = line
        elif idx == 1:
            if line.strip():
                raise ValueError("Second line should be empty")
        elif idx == 2:
            try:
                params = json.loads('\n'.join(lines[2:]))
                break
            except (TypeError, ValueError,):
                params.update(_parse_line(line))
        else:
            params.update(_parse_line(line))

    if url is None:
        raise ValueError("Cannot parse url")
    return url, params,


def do_webhook(config, resource, run, status_changed, result):
    """
    Process webhook recipients for resource

    location should be in format:

    URL

    [PAYLOAD]

    There's blank line between URL and PAYLOAD. PAYLOAD
    should be either json or list of field=value items
    in each line.

    Webhook's request is POST send to url with payload containing
    PAYLOAD
    and fields:

    ghc.result=(result of test)
    ghc.resource.url=(url of resource)
    ghc.resource.title=(title of resource)

    """
    recipients = resource.get_recipients('webhook')
    if not recipients:
        return
    for rcp in recipients:
        try:
            url, params = _parse_webhook_location(rcp)
        except ValueError as err:
            LOGGER.warning("Cannot send to {}: {}"
                           .format(rcp, err), exc_info=err)

        resource_view = '{}/resource/{}'.format(
                                            config['GHC_SITE_URL'],
                                            resource.identifier)

        params['ghc.result'] = result
        params['ghc.resource.url'] = resource.url
        params['ghc.resource.title'] = resource.title
        params['ghc.resource.type'] = resource.resource_type
        params['ghc.resource.view'] = resource_view

        try:
            r = requests.post(url, params)
            LOGGER.info("webhook deployed, got %s as reposnse",
                        r)
        except requests.exceptions.RequestException as  err:
            LOGGER.warning("cannot deploy webhook %s: %s",
                           rcp, err, exc_info=err)


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

    # run all channels, actual recipients will be filtered there
    for chann_handler in (do_email, do_webhook,):
        try:
            chann_handler(config, resource, run, status_changed, result)
        except Exception as err:
            LOGGER.warning("couldn't run notification for %s: %s",
                           chann_handler.func_name, err, exc_info=err)
