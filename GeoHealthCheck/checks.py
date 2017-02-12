import sys
from owslib.etree import etree

""" Contains basic check functions for a Probe object."""

def xml_parse(probe, args_dict):
    result = True
    msg = 'OK'
    try:
        etree.fromstring(probe.response.content)
    except:
        result = False
        msg = str(sys.exc_info())

    return result, msg


def contains_string(probe, args_dict):
    msg = 'OK'
    text = args_dict['text']
    try:
        result = text in probe.response.text
        if result is False:
            msg = '%s not in response text' % text
    except:
        result = False
        msg = str(sys.exc_info())

    return result, msg


def not_contains_string(probe, args_dict):
    result, msg = contains_string(probe, args_dict)
    if result is False and 'not in response text' in msg:
        result = True
        msg = 'OK'
    elif result is True:
        result = False
        msg = '%s in response text' % args_dict['text']

    return result, msg


def not_contains_exception(probe, args_dict):
    # TODO use Regular Expression check
    result, msg = not_contains_string(probe, {'text': 'ExceptionReport>'})
    if result is True:
        result, msg = not_contains_string(probe, {'text': 'ServiceException>'})
    return result, msg
