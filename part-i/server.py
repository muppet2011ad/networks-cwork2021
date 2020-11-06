import socket
import threading
import sys
import datetime
import atexit


def log_message(message):
    timestring = datetime.datetime.now(datetime.timezone.utc).isoformat()  # Get the timestamp as a string
    output = timestring + " - " + message + "\n"  # Create an output message
    logfile.write(output)  # Write it to the output file
    print(output, end="")  # Log it to the console


def accept_connections():
    while True:
        new_client, new_client_address = server_socket.accept()
        addresses[new_client] = new_client_address
        threading.Thread(target=handle_connection, args=(new_client,), daemon=True).start()  # Spin off connection in its own thread (set as daemon so it closes with mainthread)


def handle_connection(client):
    uname = client.recv(1024).decode()  # Client should immediately send username after connecting
    free = True
    for nick in nicks.values():  # Loop to check if nickname is free
        if uname == nick:
            free = False
            break
    if not free:
        client.send("[ERROR] Nickname already taken!\n".encode())  # Tell the client their name is taken
        log_message("[SERVER-INTERNAL] Client @ " + addresses[client][0] + "attempted to connect, but nickname was already taken.")  # Log it
        client.close()  # Disconnect the client
        del addresses[client]
        return
    nicks[client] = uname  # Set the client's nickname
    client.send(("[MOTD] " + motd + "\n").encode())  # Send the motd to the client
    log_message("[SERVER-INTERNAL] Client @ " + addresses[client][0] + ":" + str(addresses[client][1]) + " connected with nickname " + nicks[client] + ".")  # Log the connection
    send_to_all("[SERVER] " + nicks[client] + " has joined the chat.\n")

    try:
        while True:  # Mainloop to handle incoming messages
            try:
                message = client.recv(1024)
            except ConnectionResetError:  # If we error out
                message = b""  # Set the message to be blank (so it's treated as a socket close)
            message_decode = message.decode()  # Get the message and decode it
            try:
                if len(message) == 0 or message_decode == "/quit":  # If we get an empty message (socket closed) or quit command
                    announcement = "[SERVER] " + nicks[client] + " has left the chat."  # Prep announcement
                    del addresses[client]
                    del nicks[client]
                    client.close()  # Close the connection and delete all references
                    send_to_all(announcement + "\n")
                    log_message(announcement)
                    break
                elif message_decode == "test":
                    raise ValueError("test error please ignore")
                else:
                    prefixed_message = "[" + nicks[client] + "] " + message_decode
                    send_to_all(prefixed_message + "\n")
                    log_message(prefixed_message)
            except Exception as e:
                log_message("[SERVER-INTERNAL] [ERROR] " + str(e))
                client.send("[ERROR] Error processing last message.\n")
    finally:
        del addresses[client]
        del nicks[client]
        client.close()


def send_to_all(message):
    for client_sock in addresses:
        client_sock.send(message.encode())


def kill_all_connections():
    log_message("[SERVER] Server is going down.")  # Create log entry
    for client_sock in addresses:
        try:
            client_sock.send("[SERVER] Server is going down.\n".encode())  # Give a message to each client so they don't get confused
            client_sock.close()  # Close the connection
        except ConnectionResetError:  # Skip if the connection is already closed for some reason
            pass
    server_socket.shutdown(socket.SHUT_RDWR)
    server_socket.close()  # Get rid of the socket
    logfile.close()


if __name__ == "__main__":
    nicks = {}
    addresses = {}

    motd = "Dick Cheney made money from the Iraq War!"
    logfile = open("server.log", "a+")

    host = ""
    port = int(sys.argv[1])
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    log_message("[SERVER-INTERNAL] Server started. Listening on port: " + str(port))
    atexit.register(kill_all_connections)
    server_socket.listen(5)
    accept_connections()
