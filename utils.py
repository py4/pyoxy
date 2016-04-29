import socket


def parse_header(http_data):
    print http_data
    lines = http_data.splitlines()
    first_line = lines[0].split(' ')
    result = {'method': first_line[0], 'full_url': first_line[1], 'HTTP_version': first_line[2]}
    for line in lines[1:-1]:
        splitted = line.split(':', 1)
        result[splitted[0]] = splitted[1].strip()
    return result


def send_not_implemented(connection):
    result = "HTTP/1.1 501 Not Implemented\n"
    result += "Date: Thu, 20 May 2004 21:12:58 GMT\n"
    result += "Connection: close\n"
    result += "Server: Python/6.6.6 (custom)\n"
    connection.send(result)


def call_server(url, data, buffer_size):
    data = data.replace("HTTP/1.1", "HTTP/1.0")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((url, 80))
    s.send(data)
    result = ""
    while True:
        reply = s.recv(buffer_size)
        if len(reply) > 0:
            result += reply
        else:
            break
    s.close()
    return result
