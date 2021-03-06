# -*- coding: utf-8 -*-
'''
Support for the Amazon Simple Queue Service.
'''
import json

# Import salt libs
import salt.utils

_OUTPUT = '--output json'


def __virtual__():
    if salt.utils.which('aws'):
        # awscli is installed, load the module
        return True
    return False


def _region(region):
    '''
    Return the region argument.
    '''
    return ' --region {r}'.format(r=region)


def _run_aws(cmd, region, opts, user, **kwargs):
    '''
    Runs the given command against AWS.
    cmd
        Command to run
    region
        Region to execute cmd in
    opts
        Pass in from salt
    user
        Pass in from salt
    kwargs
        Key-value arguments to pass to the command
    '''
    _formatted_args = [
        '--{0} "{1}"'.format(k, v) for k, v in kwargs.iteritems()]

    cmd = 'aws sqs {cmd} {args} {region} {out}'.format(
        cmd=cmd,
        args=' '.join(_formatted_args),
        region=_region(region),
        out=_OUTPUT)

    rtn = __salt__['cmd.run'](cmd, runas=user)

    return json.loads(rtn) if rtn else ''


def list_queues(region, opts=None, user=None):
    '''
    List the queues in the selected region.

    region
        Region to list SQS queues for

    opts : None
        Any additional options to add to the command line

    user : None
        Run hg as a user other than what the minion runs as
    '''
    out = _run_aws('list-queues', region, opts, user)

    ret = {
        'retcode': 0,
        'stdout': out['QueueUrls'],
    }
    return ret


def create_queue(name, region, opts=None, user=None):
    '''
    Creates a queue with the correct name.

    name
        Name of the SQS queue to create

    region
        Region to create the SQS queue in

    opts : None
        Any additional options to add to the command line

    user : None
        Run hg as a user other than what the minion runs as
    '''

    create = {'queue-name': name}
    out = _run_aws(
        'create-queue', region=region, opts=opts,
        user=user, **create)

    ret = {
        'retcode': 0,
        'stdout': out['QueueUrl'],
        'stderr': '',
    }
    return ret


def delete_queue(name, region, opts=None, user=None):
    '''
    Deletes a queue in the region.

    name
        Name of the SQS queue to deletes
    region
        Name of the region to delete the queue from

    opts : None
        Any additional options to add to the command line

    user : None
        Run hg as a user other than what the minion runs as
    '''
    queues = list_queues(region, opts, user)
    url_map = _parse_queue_list(queues)

    import logging
    logger = logging.getLogger(__name__)
    logger.debug('map ' + unicode(url_map))
    if name in url_map:
        delete = {'queue-url': url_map[name]}

        _run_aws(
            'delete-queue',
            region=region,
            opts=opts,
            user=user,
            **delete)
        success = True
        err = ''
        out = '{0} deleted'.format(name)

    else:
        out = ''
        err = "Delete failed"
        success = False

    ret = {
        'retcode': 0 if success else 1,
        'stdout': out,
        'stderr': err,
    }
    return ret


def queue_exists(name, region, opts=None, user=None):
    '''
    Returns True or False on whether the queue exists in the region

    name
        Name of the SQS queue to search for

    region
        Name of the region to search for the queue in

    opts : None
        Any additional options to add to the command line

    user : None
        Run hg as a user other than what the minion runs as
    '''
    output = list_queues(region, opts, user)

    return name in _parse_queue_list(output)


def _parse_queue_list(list_output):
    '''
    Parse the queue to get a dict of name -> URL
    '''
    queues = dict((q.split('/')[-1], q) for q in list_output['stdout'])
    return queues
