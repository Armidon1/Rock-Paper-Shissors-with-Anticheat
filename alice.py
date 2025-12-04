import secrets
import socket
from hashlib import sha256
from tcp_json import send_json
from tcp_json import receive_json

HOST = '0.0.0.0'
PORT = 8080

my_move = ""
my_nonce = ""
bob_move = ""

def determine_winner(my_move, bob_move):
    a = my_move.lower()
    b = bob_move.lower()
    print(f"[Alice] Determining winner: Me({a}) vs Bob({b})")  # Debug
    
    valid_moves = ["rock", "paper", "scissors"]
    
    if a not in valid_moves or b not in valid_moves:
        return "Error: Invalid Move"

    if a == b:
        return "Draw"

    if (a == "rock" and b == "scissors") or \
       (a == "scissors" and b == "paper") or \
       (a == "paper" and b == "rock"):
        return "Me"
    
    return "Bob"

def handle_bob_move(message, conn):
    global bob_move
    bob_move = message.get("value")
    print(f"[Alice] Received Bob's move: {bob_move}")
    
    commitment_check = sha256((my_move + my_nonce).encode()).hexdigest()
    print(f"[Alice] My commitment: {commitment_check}")
    
    print("[Alice] Commitment verified successfully!")
    winner = determine_winner(my_move, bob_move)
    print(f"[Alice] The winner is: {winner}")
    if winner == "Bob":
        print("[Alice] Should I send the nonce to Bob? I can escape...(yes/no)")
        choice = input().strip().lower()
        if choice == "yes":
            response = {
                "type": "reveal-nonce",
                "value": my_nonce
            }
            send_json(conn, response)
            print("[alice] Sent nonce to Bob.")
        else:
            print("[alice] I chose not to send the nonce to Bob. I have to run!")
    else:
        response = {
            "type": "reveal-nonce",
            "value": my_nonce
        }
        send_json(conn, response)
        print("[alice] Sent nonce to Bob.")
    return False
    

def game(message, conn):
    global my_move, my_nonce
    my_move = secrets.choice(["Rock", "Paper", "Scissors"])
    my_nonce = secrets.token_hex(16)
    commitment = sha256((my_move + my_nonce).encode()).hexdigest()
    message = {
        "type" : "game-commitment",
        "value" : commitment
    }
    
    send_json(conn, message)
    print(f"[Alice] Sent my move ({my_move}) without nonce ({my_nonce}), I want to be sure that Bob cannot cheat")
    return True
    

def handle(message, conn):
    msg_type = message.get("type")
    match msg_type:
        case "game":
            return game(message, conn)
        case "bob-move":
            return handle_bob_move(message, conn)
            

def main():

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conn:
        print("[Alice] I'm going to meet Bob...")
        conn.connect((HOST, PORT))
        print("[Alice] Arrivede to Bob.")

        while True:
            print("[Alice] Waiting for message...")
            # Do not pass 0 here; pass no message (or None) so the function reads from socket
            message = receive_json(conn)
            if not message:
                print("[Alice] No message received, closing connection")
                break
            #print(f"message received : {message}")
            if handle(message, conn) == False:
                break
        conn.close()
        print("[Alice] game over, connection closed.")
    

if __name__ == "__main__":
    main()