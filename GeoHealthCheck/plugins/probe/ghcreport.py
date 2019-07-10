import logging
from email.mime.text import MIMEText
from email.utils import formataddr

from flask_babel import gettext

from GeoHealthCheck.init import App
from GeoHealthCheck.probe import Probe
from GeoHealthCheck.result import Result
from GeoHealthCheck.util import render_template2, send_email

LOGGER = logging.getLogger(__name__)


class GHCEmailReporter(Probe):
    """
    Probe for GeoHealthCheck endpoint recurring status Reporter.
    When invoked it will get the overall status of the GHC Endpoint and email
    a summary, with links to more detailed reports.
    """

    NAME = 'GHC Email Reporter'

    DESCRIPTION = 'Fetches Resources status summary ' \
                  'from GHC endpoint and reports by email'

    RESOURCE_TYPE = 'GHC:Report'

    REQUEST_METHOD = 'GET'

    PARAM_DEFS = {
        'email': {
            'type': 'string',
            'description': 'A comma-separated list of email addresses \
                           to send status report to',
            'default': None,
            'required': True
        }
    }

    """Param defs"""

    def __init__(self):
        Probe.__init__(self)

    def perform_request(self):
        """
        Perform the reporting.
        """

        # Be sure to use bare root URL http://.../FeatureServer
        ghc_url = self._resource.url.split('?')[0]

        # Assemble request templates with root FS URL

        summary_url = ghc_url + '/api/v1.0/summary/'

        # 1. Get the summary (JSON) report from GHC endpoint
        result = Result(True, 'Get GHC Report')
        result.start()
        try:
            response = self.perform_get_request(summary_url)
            status = response.status_code
            overall_status = status / 100
            if overall_status in [4, 5]:
                raise Exception('HTTP Error status=%d reason=%s'
                                % (status, response.reason))

            summary_report = response.json()
        except Exception as err:
            msg = 'Cannot get summary from %s err=%s' % \
                  (summary_url, str(err))
            result.set(False, msg)
            result.stop()
            self.result.add_result(result)
            return

        # ASSERTION - summary report fetch ok

        # 2. Do email reporting with summary report
        result = Result(True, 'Send Email')
        result.start()

        try:
            config = App.get_config()

            # Create message body with report
            template_vars = {
                'summary': summary_report,
                'config': config
            }

            msg_body = render_template2(
                'status_report_email.txt', template_vars)

            resource = self._resource
            to_addrs = self._parameters.get('email', None)
            if to_addrs is None:
                raise Exception(
                    'No emails set for GHCEmailReporter in resource=%s' %
                    resource.identifier)

            to_addrs = to_addrs.replace(' ', '')
            if len(to_addrs) == 0:
                raise Exception(
                    'No emails set for GHCEmailReporter in resource=%s' %
                    resource.identifier)

            to_addrs = to_addrs.split(',')
            msg = MIMEText(msg_body, 'plain', 'utf-8')
            msg['From'] = formataddr((config['GHC_SITE_TITLE'],
                                      config['GHC_ADMIN_EMAIL']))
            msg['To'] = ', '.join(to_addrs)
            msg['Subject'] = '[%s] %s' % (config['GHC_SITE_TITLE'],
                                          gettext('Status summary'))

            from_addr = '%s <%s>' % (config['GHC_SITE_TITLE'],
                                     config['GHC_ADMIN_EMAIL'])

            msg_text = msg.as_string()
            send_email(config['GHC_SMTP'], from_addr, to_addrs, msg_text)
        except Exception as err:
            msg = 'Cannot send email. Contact admin: '
            LOGGER.warning(msg + ' err=' + str(err))
            result.set(False, 'Cannot send email: %s' % str(err))

        result.stop()

        # Add to overall Probe result
        self.result.add_result(result)
