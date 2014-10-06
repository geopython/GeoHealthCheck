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


def average(values):
    """calculates average from a list"""

    return float(sum(values) / len(values))


def percentage(number, total):
    """calculates a percentage"""

    if total == 0:  # no resources registered yet
        return 0.00

    percentage_value = float((float(float(number)/float(total)))*100.0)
    if percentage_value in [0.0, 100.0]:
        return int(percentage_value)
    return percentage_value


def get_python_snippet(resource):
    """return sample interactive session"""

    lines = []
    lines.append('# testing via OWSLib')
    lines.append('# test GetCapabilities')
    if resource.resource_type == 'OGC:WMS':
        lines.append('from owslib.wms import WebMapService')
        lines.append('myows = WebMapService(\'%s\')' % resource.url)
    elif resource.resource_type == 'OGC:CSW':
        lines.append('from owslib.csw import CatalogueServiceWeb')
        lines.append('myows = CatalogueServiceWeb(\'%s\')' % resource.url)
    lines.append('myows.identification.title\n\'%s\'' % resource.title)
    return '\n>>> '.join(lines)
