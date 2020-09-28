import json
from common.constants import*
from common.errors import IncorrectDataRecivedError, NonDictInputError
from common.decorators import log


@log
def get_message(client):
    encoded_response = client.recv(MAX_PACKAGE_SIZE)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode(ENCODING)
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        else:
            raise IncorrectDataRecivedError
    else:
        raise IncorrectDataRecivedError


@log
def send_message(sock, message):
    if not isinstance(message, dict):
        raise NonDictInputError
    json_message = json.dumps(message)
    encoded_message = json_message.encode(ENCODING)
    sock.send(encoded_message)
