# GNU MediaGoblin -- federated, autonomous media hosting
# Copyright (C) 2011, 2012 MediaGoblin contributors.  See AUTHORS.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging

from celery import registry
from celery.task import Task

from mediagoblin.tools.mail import send_email
from mediagoblin.db.models import CommentNotification


_log = logging.getLogger(__name__)


class EmailNotificationTask(Task):
    '''
    Celery notification task.

    This task is executed by celeryd to offload long-running operations from
    the web server.
    '''
    def run(self, notification_id, message):
        cn = CommentNotification.query.filter_by(id=notification_id).first()
        _log.info(u'Sending notification email about {0}'.format(cn))

        return send_email(
            message['from'],
            [message['to']],
            message['subject'],
            message['body'])

email_notification_task = registry.tasks[EmailNotificationTask.name]
