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
import models
import util
from sqlalchemy import text
from plugin import Plugin
from factory import Factory
from init import App
APP = App.get_app()

LOGGER = logging.getLogger(__name__)


def list_resources(resource_type=None, query=None, tag=None):
    """return all resources"""

    reliability_values = []
    first_run = None
    last_run = None

    response = {
        'total': 0,
        'success': {
            'number': 0,
            'percentage': 0
        },
        'fail': {
            'number': 0,
            'percentage': 0
        },
        'first_run': None,
        'last_run': None,
        'reliability': 0
    }

    filters = ()

    if resource_type is not None:
        filters = filters + (text("resource_type = '%s'" % resource_type),)

    if query is not None:
        field, term = get_query_field_term(query)
        filters = filters + (field.ilike(term),)

    if tag is not None:
        tag_filter = (models.Resource.tags.any(models.Tag.name.in_([tag])),)
        filters = filters + tag_filter

    response['resources'] = models.Resource.query.filter(*filters).all()

    response['total'] = len(response['resources'])
    response['success']['percentage'] = 0
    response['fail']['percentage'] = 0
    response['reliability'] = 0
    for resource in response['resources']:
        if resource.runs.count() > 0:
            # View should work even without Runs
            if  first_run is None or resource.first_run < first_run:
                first_run = resource.first_run
            if last_run is None or resource.last_run < last_run:
                last_run = resource.last_run
            response['first_run'] = first_run
            response['last_run'] = last_run
            if resource.last_run.success:
                response['success']['number'] += 1
            else:
                response['fail']['number'] += 1

            reliability_values.append(resource.reliability)

    response['success']['percentage'] = int(round(util.percentage(
        response['success']['number'], response['total'])))
    response['fail']['percentage'] = 100 - response['success']['percentage']
    response['reliability'] = round(util.average(reliability_values), 1)

    return response


def get_resource_by_id(identifier):
    """return one resource by identifier"""
    return models.Resource.query.filter_by(
        identifier=identifier).first_or_404()


def get_run_by_id(identifier):
    """return one Run by identifier"""
    return models.Run.query.filter_by(
        identifier=identifier).first_or_404()


def get_run_by_resource_id(identifier):
    """return one Run by identifier"""
    return models.Run.query.filter_by(
        resource_identifier=identifier)


def get_resource_types_counts():
    """return frequency counts of registered resource types"""

    mrt = models.get_resource_types_counts()
    return {
        'counts': mrt[0],
        'total': mrt[1]
    }


def get_health_summary():
    """return summary of all runs"""

    # For overall reliability
    total_runs = models.get_runs_count()
    failed_runs = models.get_runs_status_count(False)
    success_runs = total_runs - failed_runs

    # Resources status derived from last N runs
    total_resources = models.get_resources_count()
    last_runs = models.get_last_run_per_resource()
    failed = 0
    failed_resources = []
    for run in last_runs:
        if not run.success:
            failed_resources.append(
                get_resource_by_id(run.resource_identifier))
            failed += 1

    success = total_resources - failed

    failed_percentage = int(round(
        util.percentage(failed, total_resources)))
    success_percentage = 100 - failed_percentage

    response = {
        'site_url': APP.config['GHC_SITE_URL'],
        'total': total_resources,
        'success': {
            'number': success,
            'percentage': success_percentage
        },
        'fail': {
            'number': failed,
            'percentage': failed_percentage
        },
        'first_run': models.get_first_run(),
        'last_run': models.get_last_run(),
        'reliability': round(util.percentage(success_runs, total_runs), 1),
        'failed_resources': failed_resources
    }

    return response


def get_tag_counts():
    """return all tag counts"""

    return models.get_tag_counts()


def get_query_field_term(query):
    """determine query context from q="""

    field = models.Resource.title  # default

    try:
        facet, term = query.split(':')
        term2 = '%%%s%%' % term  # default like
        if facet == 'url':
            field = models.Resource.url
        elif facet == 'title':
            field = models.Resource.title
        elif facet == 'site':
            field = models.Resource.url
            term2 = '%%%s/%%' % term
        elif facet == 'owner':
            field = models.Resource.owner_identifier
        term = term2
    except ValueError:  # default search
        term = '%%%s%%' % query

    return [field, term]


def get_probes_avail(resource_type=None, resource=None):
    """
    Get all available Probes with their attributes.
    :param resource_type: optional resource type e.g. OGC:WMS
    :param resource: optional Resource instance
    :return:
    """

    # Assume no resource type
    filters = None
    if resource_type:
        filters = [('RESOURCE_TYPE', resource_type),
                   ('RESOURCE_TYPE', '*:*')]

    probe_classes = Plugin.get_plugins('GeoHealthCheck.probe.Probe', filters)

    result = dict()
    for probe_class in probe_classes:
        probe = Factory.create_obj(probe_class)
        if probe:
            if resource:
                try:
                    probe.expand_params(resource)
                except Exception as err:
                    msg = 'Cannot expand plugin vars for %s err=%s' \
                          % (probe_class, str(err))
                    LOGGER.warning(msg)

            result[probe_class] = probe.get_plugin_vars()

    return result
