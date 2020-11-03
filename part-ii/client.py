import socket
import threading
import sys
import tkinter
from tcp_helpers import *

nickname = sys.argv[1]
host = sys.argv[2]
port = int(sys.argv[3])  # Grab all command line arguments we need


def handle_receive():
    while True:  # Mainloop for receiving data
        global nickname
        message = long_receive(sock).decode()  # Receive message and decode it into a string
        if len(message) == 0:  # If the socket reads no bytes, the server closed the connection
            entry_box.config(state=tkinter.DISABLED)  # Disable the entry box to prevent further message sending
            return  # And quit out the receive thread
        elif message.startswith("[SERVER] " + nickname + " has changed name to "):
            nickname = message.split()[6][:-1]
            tk.title("MSN Messenger Redux - Connected to " + host + ":" + str(port) + " as " + nickname)
        elif message == "/err":
            message = "[ERROR] Error receiving message from server."
        if message_scrollbar.get()[1] == 1.0:  # If the scrollbar is at the end
            auto_scroll = True  # Set autoscroll
        else:
            auto_scroll = False  # Otherwise we don't want to autoscroll
        message_text.config(state=tkinter.NORMAL)  # Enable text editing briefly
        message_text.insert(tkinter.END, message + "\n")  # Insert the message
        if auto_scroll:
            message_text.see(tkinter.END)  # Keep at the end of the text box if we're autoscrolling
        message_text.config(state=tkinter.DISABLED)  # Go back to disabled


def handle_send(event=None):
    message = entry_string.get()  # Get the message the user intended to send
    entry_string.set("")  # Clear the text entry
    long_send(sock, message.encode())  # Send the message to the server
    if message == "/quit":  # If the message is quit
        sock.close()  # Close the connection
        tk.quit()  # Kill the thread


def window_close(event=None):  # Called if the user closes the window
    sock.send("/quit".encode())  # Send a quit message to the server for it to close the connection


# Horrible GUI stuff
tk = tkinter.Tk()
tk.title("MSN Messenger Redux - Connected to " + host + ":" + str(port) + " as " + nickname)

entry_string = tkinter.StringVar()  # Stores the user's input of messages
entry_string.set("")  # Default as empty
entry_box = tkinter.Entry(tk, textvariable=entry_string)  # Creates an entry widget for them to use
entry_box.bind("<Return>", handle_send)  # Send on enter

message_frame = tkinter.Frame(tk)  # Make a frame to keep the message log and scrollbar together
message_scrollbar = tkinter.Scrollbar(message_frame)
message_text = tkinter.Text(message_frame, height=20, width=80, yscrollcommand=message_scrollbar.set)  # Make both widgets
message_text.insert("0.0", "Type below and hit enter to start chatting. Type /quit to quit (it's even easier than Vim!)\n---------------------\n")
# Instruction text
message_text.config(state=tkinter.DISABLED)  # Disable the text box so the user can't type there

message_scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
message_text.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
message_frame.pack()
entry_box.pack(fill=tkinter.X)  # Pack everything into the GUI

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((host, port))  # Connect to the server
threading.Thread(target=handle_receive, daemon=True).start()  # Start the receiving thread
long_send(sock, nickname.encode())  # Send the nickname

tkinter.mainloop()  # Open the GUI
