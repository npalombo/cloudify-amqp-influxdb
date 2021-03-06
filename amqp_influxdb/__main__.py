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

import argparse

from amqp_influxdb import (InfluxDBPublisher, AMQPTopicConsumer)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--amqp-exchange', required=True)
    parser.add_argument('--amqp-routing-key', required=True)
    parser.add_argument('--influx-database', required=True)
    return parser.parse_args()


def main():
    args = parse_args()

    publisher = InfluxDBPublisher(
        database=args.influx_database)
    consumer = AMQPTopicConsumer(
        exchange=args.amqp_exchange,
        routing_key=args.amqp_routing_key,
        message_processor=publisher.process)
    consumer.consume()


if __name__ == '__main__':
    main()
