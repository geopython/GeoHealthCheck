# coding=utf-8
# =================================================================
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
# Just van den Broecke <justb4@gmail.com>
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
import os
import random
import string
from models import Resource, ResourceLock, flush_runs
from healthcheck import run_resource
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import JobLookupError
from init import App

LOGGER = logging.getLogger(__name__)
DB = App.get_db()

# Create scheduler
scheduler = BackgroundScheduler()


# commit or rollback shorthand
def db_commit():
    err = None
    try:
        DB.session.commit()
    except Exception as err:
        DB.session.rollback()
    # finally:
    #     DB.session.close()
    return err


def run_job(resource_id, frequency):
    # Generate unique id
    # https://stackoverflow.com/questions/2257441/random-string-generation-with-upper-case-letters-and-digits-in-python
    uuid = '%d-%s' % (os.getpid(), ''.join(random.choice(
        string.ascii_uppercase + string.digits) for _ in range(8)))

    resource = Resource.query.filter_by(identifier=resource_id).first()

    if not resource:
        stop_job(resource_id)
        return

    lock = ResourceLock.query.filter_by(identifier=resource_id).first()

    if not lock:
        # No lock at all on Resource: (hope) we're first
        # obtain fresh lock, back-off if failed
        LOGGER.info('%d No Lock at all: obtain new' % resource_id)

        lock = ResourceLock(resource, uuid, frequency)
        DB.session.add(lock)
        lock_err = db_commit()
        if lock_err:
            # Another process may have been there first!
            LOGGER.info('%d Cannot obtain Lock %s' %
                        (resource_id, str(lock_err)))
            return
    else:
        # Lock is there, look if available
        LOGGER.info('%d Lock avail: try obtaining..' % resource_id)
        if not lock.obtain(uuid, frequency):
            LOGGER.info('%d Cannot obtain' % resource_id)
            return
        else:
            LOGGER.info('%d Lock obtained, delete and renew' % resource_id)
            DB.session.delete(lock)
            lock_err = db_commit()
            if lock_err:
                # Another process may have been there first!
                LOGGER.info('%d Lock Delete failed' % resource_id)
                return

            LOGGER.info('%d Lock deleted, add new' % resource_id)
            # (hope) we're first
            # obtain fresh lock, back-off if failed
            lock = ResourceLock(resource, uuid, frequency)
            DB.session.add(lock)
            lock_err = db_commit()
            if lock_err:
                # Another process may have been there first!
                LOGGER.info('%d Lock Add failed' % resource_id)
                return

            # Check if we really own the lock
            LOGGER.info('%d Lock Add OK' % resource_id)
            lock = ResourceLock.query.filter_by(
                identifier=resource_id).first()

            if lock.owner != uuid:
                LOGGER.info('%d Lock Add OK, not owner: back-off'
                            % resource_id)
                return

    if lock:
        try:
            run_resource(resource_id)
            LOGGER.info('%d run_resource OK' % resource_id)
        finally:
            pass


def start_schedule():
    # Cold start every cron of every Resource
    for resource in Resource.query.all():
        add_job(resource)

    # change configuration
    scheduler.configure(job_defaults={
        'coalesce': False,
        'max_instances': 100000
    })

    scheduler.add_job(flush_runs, 'interval', minutes=60)
    scheduler.add_job(check_schedule, 'interval', minutes=5)

    scheduler.start()
    import atexit
    atexit.register(lambda: stop_schedule())


def check_schedule():
    LOGGER.info('Checking Job schedules')
    # Check the schedule for changed jobs
    for resource in Resource.query.all():
        job = scheduler.get_job(str(resource.identifier))
        if job is None:
            add_job(resource)

        current_freq = job.args[1]

        # Run frequency changed?
        if current_freq != resource.run_frequency:
            # Reschedule Job
            update_job(resource)


def update_job(resource):
    stop_job(resource.identifier)

    # Add job to Scheduler
    add_job(resource)


def add_job(resource):
    LOGGER.info('Starting job for resource=%d' % resource.identifier)
    freq = resource.run_frequency

    scheduler.add_job(
        run_job, 'interval', args=[resource.identifier, freq],
        minutes=freq,
        id=str(resource.identifier))


def stop_job(resource_id):
    LOGGER.info('Stopping job for resource=%d' % resource_id)

    # Try to remove job from scheduler
    try:
        scheduler.remove_job(str(resource_id))
    except JobLookupError:
        pass


def stop_schedule():
    LOGGER.info('Stopping Scheduler')
    scheduler.shutdown()


if __name__ == '__main__':
    import time

    # Start scheduler
    start_schedule()

    while True:
        print("This prints once a minute.")
        time.sleep(60)  # Delay for 1 minute (60 seconds).
