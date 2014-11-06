########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
############

import threading
import json
import logging

from tornado import httputil, httpclient, ioloop
import pika


logging.basicConfig()
logger = logging.getLogger('amqp_influx')


class AMQPTopicConsumer(object):

    def __init__(self,
                 exchange,
                 routing_key,
                 message_processor,
                 connection_parameters=None):
        self.message_processor = message_processor

        connection_parameters = connection_parameters or {}
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(**connection_parameters))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=exchange,
                                      type='topic',
                                      durable=False,
                                      auto_delete=True,
                                      internal=False)
        result = self.channel.queue_declare(
            auto_delete=True,
            durable=False,
            exclusive=False)
        queue = result.method.queue
        self.channel.queue_bind(exchange=exchange,
                                queue=queue,
                                routing_key=routing_key)
        self.channel.basic_consume(self._process,
                                   queue,
                                   no_ack=True)

    def consume(self):
        self.channel.start_consuming()

    def _process(self, channel, method, properties, body):
        try:
            parsed_body = json.loads(body)
            self.message_processor(parsed_body)
        except Exception as e:
            logger.warn('Failed message processing: {0}'.format(e))


def handle_request(response):
    if response.error:
        print "Error:", response.error


class InfluxDBPublisher(object):

    columns = ["value", "unit", "type"]

    def __init__(self,
                 database,
                 host='localhost',
                 port=8086,
                 user='root',
                 password='root'):

        url = 'http://{0}:{1}/db/{2}/series'.format(host, port, database)
        qs = {'u': user, 'p': password}
        self.url = httputil.url_concat(url, qs)
        self.client = httpclient.AsyncHTTPClient()

        def start():
            ioloop.IOLoop.instance().start()

        thread = threading.Thread(target=start)
        thread.daemon = True
        thread.start()

    def process(self, body):
        data = json.dumps(self._build_body(body))
        self.client.fetch(self.url,
                          handle_request,
                          body=data,
                          method='POST',
                          headers={
                              'Content-Type': 'application/json'
                          })

    def _build_body(self, body):
        return [{
            'name': self._name(body),
            'points': self._points(body),
            'columns': self.columns,
        }]

    def _name(self, body):
        return '{0}.{1}.{2}.{3}_{4}'.format(
            body['deployment_id'],
            body['node_name'],
            body['node_id'],
            body['name'],
            body['path'])

    def _points(self, body):
        return [[body['metric'], body['unit'], body['type']]]
