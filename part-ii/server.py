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


def find_nick(nick): # Quick and dirty linear search to get client from nickname
    for client, nickname in nicks.items():
        if nickname == nick:
            return client
    return None


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

    while True:  # Mainloop to handle incoming messages
        try:
            message = client.recv(1024)
        except ConnectionResetError:  # If we error out
            message = b""  # Set the message to be blank (so it's treated as a socket close)
        message_decode = message.decode()  # Get the message and decode it
        if len(message) == 0 or message_decode == "/quit":  # If we get an empty message (socket closed) or quit command
            announcement = "[SERVER] " + nicks[client] + " has left the chat."  # Prep announcement
            del addresses[client]
            del nicks[client]
            client.close()  # Close the connection and delete all references
            send_to_all(announcement + "\n")
            log_message(announcement)
            break
        elif message_decode.startswith("/whis"): # Whisper function
            target_client = find_nick(message_decode.split()[1]) # Finds the client with the target nickname
            if not target_client: # If the target is None
                client.send("[ERROR] User not found!\n".encode()) # Inform the user as such
                continue # Stop dealing with this message
            message_body = message_decode[6:].partition(" ")[2] # Get body of the message
            prefixed_message = "[" + nicks[client] + "] [WHISPER] " + message_body # Apply prefix and whisper tag
            target_client.send((prefixed_message + "\n").encode()) # Send whisper to target
            client.send(("[SERVER] Whisper to " + nicks[target_client] + " sent.\n").encode()) # Send confirmation of whisper to sender
            log_message(nicks[client] + " whispered to " + nicks[target_client]) # Log the occurrence of a whisper
        elif message_decode.startswith("/here"): # Command to get connected clients
            response_body = "\n\t".join(nicks.values()) # Get list of clients
            client.send(("[SERVER] Connected Clients:\n\t" + response_body + "\n").encode()) # Send that to the client
            log_message(nicks[client] + " requested a list of clients.") # Log invocation of command
        else:
            prefixed_message = "[" + nicks[client] + "] " + message_decode
            send_to_all(prefixed_message + "\n")
            log_message(prefixed_message)


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
