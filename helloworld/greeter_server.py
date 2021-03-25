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


import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN_TXT_PATH = os.path.sep.join([BASE_DIR, 'filter', 'domain.txt'])


class Greeter(helloworld_pb2_grpc.GreeterServicer):

    def SayHello(self, request, context):
        if (request.name.startswith('CHECK')):
            sender_address = request.name.split(':')[1]
            with open(DOMAIN_TXT_PATH, 'r') as f:
                all_lines = f.readlines()
                found = False
                for line in all_lines:
                    if line.rstrip('\n') == sender_address:
                        found = True
                        break
                
                if found:
                    return helloworld_pb2.HelloReply(message=f'KNOWN {sender_address}')
                else:
                    return helloworld_pb2.HelloReply(message=f'UNKNOWN {sender_address}')


        return helloworld_pb2.HelloReply(message='INVALID COMMAND')


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    helloworld_pb2_grpc.add_GreeterServicer_to_server(Greeter(), server)
    server.add_insecure_port('172.105.208.30:50051')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()
    serve()
