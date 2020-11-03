def long_receive(socket):
    message_len_str = socket.recv(8)
    if len(message_len_str) == 0:
        return b""
    else:
        try:
            message_len = int(message_len_str)
        except ValueError:
            return "/err".encode()
        if message_len <= 1024:
            return socket.recv(message_len)
        message = b""
        while message_len > 1024:
            message += socket.recv(1024)
            message_len -= 1024
        return message + socket.recv(message_len)

def long_send(socket, message):
    message_len = len(message)
    to_send = str(message_len).zfill(8).encode() + message
    socket.sendall(to_send)