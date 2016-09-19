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

import models
import util


def list_resources(resource_type=None, query=None):
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

    if resource_type is not None:
        response['resources'] = models.Resource.query.filter_by(
            resource_type=resource_type).all()

    if query is not None:
        field, term = get_query_field_term(query)
        response['resources'] = models.Resource.query.filter(
            field.ilike(term)).all()

    if 'resources' not in response:
        # No query nor resource_type provided: fetch all resources
        response['resources'] = models.Resource.query.all()

    response['total'] = len(response['resources'])
    for resource in response['resources']:
        if resource.first_run < first_run or first_run is None:
            first_run = resource.first_run
        if resource.last_run < last_run or last_run is None:
            last_run = resource.last_run
        response['first_run'] = first_run
        response['last_run'] = last_run
        if resource.last_run.success:
            response['success']['number'] += 1
        else:
            response['fail']['number'] += 1
        reliability_values.append(resource.reliability)

    response['success']['percentage'] = util.percentage(
        response['success']['number'], response['total'])
    response['fail']['percentage'] = util.percentage(
        response['fail']['number'], response['total'])
    response['reliability'] = util.average(reliability_values)

    return response


def get_resource_by_id(identifier):
    """return one resource by identifier"""
    return models.Resource.query.filter_by(
        identifier=identifier).first_or_404()


def get_resource_types_counts():
    """return frequency counts of registered resource types"""

    mrt = models.get_resource_types_counts()
    return {
        'counts': mrt[0],
        'total': mrt[1]
    }


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
