# Copyright 2015 gRPC authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The Python implementation of the GRPC helloworld.Greeter server."""

from concurrent import futures
import logging

import grpc

import helloworld_pb2
import helloworld_pb2_grpc


import psycopg2

import datetime


class Greeter(helloworld_pb2_grpc.GreeterServicer):

    def SayHello(self, request, context):
        if request.name.startswith('CHECK') or request.name.startswith('SETKNOWN') or request.name.startswith('SETUNKNOWN'):
            sender_address = request.name.split(':')[1]

            try:
                if conn.closed:
                    connect_db()
            except NameError:
                connect_db()

            start_time = datetime.datetime.now()
            try:
                with conn.cursor() as cursor:

                    if request.name.startswith('CHECK'):
                        cursor.execute(f'SELECT count(*) FROM known_sender WHERE address = \'{sender_address}\'')
                        records = cursor.fetchall()

                        match_count = records[0][0]
                        logger.info(f'match_count is {match_count}')
    
                        cursor.close()
    
                        logger.info(f'Time elapsed for fetching records: {datetime.datetime.now() - start_time}')
    
                        if match_count == 0:
                            return helloworld_pb2.HelloReply(message=f'UNKNOWN {sender_address}')
                        else:
                            return helloworld_pb2.HelloReply(message=f'KNOWN {sender_address}')

                    elif request.name.startswith('SETKNOWN'):
                        cursor.execute(f'INSERT INTO known_sender VALUES (\'{sender_address}\')')
                        cursor.close()
                        conn.commit()

                    elif request.name.startswith('SETUNKNOWN'):
                        cursor.execute(f'DELETE FROM known_sender WHERE address = \'{sender_address}\'')
                        cursor.close()
                        conn.commit()

            finally:
                if conn:
                    if datetime.datetime.now() - datetime.timedelta(seconds=1800) > connect_db_time:
                        conn.close()

        return helloworld_pb2.HelloReply(message='INVALID COMMAND')


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    helloworld_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)
    server.add_insecure_port('172.105.208.30:50051')
    server.start()
    server.wait_for_termination()

def create_logger():
    global logger

    logging.basicConfig()
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    if not len(logger.handlers) == 0:
        logger.handlers.clear()

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh = logging.FileHandler('console.log', mode='w', encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)   

def connect_db():
    global conn

    start_time = datetime.datetime.now()
    try:
        conn = psycopg2.connect("dbname='eguard' user='eguard_admin' host='dev.clo3yq4mhvjy.ap-east-1.rds.amazonaws.com' password='eguardbymichael'")
    except:
        logger.error("I am unable to connect to the database")

    global connect_db_time
    connect_db_time = datetime.datetime.now()
    logger.info(f'Time elapsed for connecting to the database: {datetime.datetime.now() - start_time}')

if __name__ == '__main__':
    create_logger()
    serve()
