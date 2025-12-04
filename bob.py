import socket
import secrets
from hashlib import sha256
from tcp_json import send_json
from tcp_json import receive_json
from time import sleep

HOST = "0.0.0.0"
PORT = 8080

alice_commitment = ""
my_move = ""
alice_nonce = ""

def determine_winner(alice_move, my_move):
    a = alice_move.lower()
    b = my_move.lower()
    print(f"[Bob] Determining winner: Alice({a}) vs Me({b})")  # Debug
    
    valid_moves = ["rock", "paper", "scissors"]
    
    if a not in valid_moves or b not in valid_moves:
        return "Error: Invalid Move"

    if a == b:
        return "Draw"

    if (a == "rock" and b == "scissors") or \
       (a == "scissors" and b == "paper") or \
       (a == "paper" and b == "rock"):
        return "Alice"
    
    return "Me"

def handle_game_commitment(message, conn):
    global alice_commitment
    alice_commitment = message.get("value")
    print(f"[BOB] Received Alice's commitment: {alice_commitment}")
    
    global my_move
    my_move = secrets.choice(["Rock", "Paper", "Scissors"])
    print(f"[BOB] My move is: {my_move}")
    
    response = {
        "type": "bob-move",
        "value": my_move
    }
    send_json(conn, response)
    print(f"[BOB] Sent my move to Alice.")   
    conn.settimeout(5.0)     
    print("[BOB] Waiting 5 seconds for Alice to reveal nonce...")

def handle_reveal_nonce(message):
    global alice_nonce
    alice_nonce = message.get("value")
    print(f"[BOB] Received Alice's nonce: {alice_nonce}")
    
    check = False
    for alice_move in ["Rock", "Paper", "Scissors"]:
        commitment_check = sha256((alice_move + alice_nonce).encode()).hexdigest()
        if commitment_check == alice_commitment:
            check = True
            break
    
    if check:
        print(f"[BOB] Alice move: {alice_move}")
    else:
        print("[BOB] Could not determine Alice's move from the nonce!")
        return False
    
    winner = determine_winner(alice_move, my_move)
    print(f"[BOB] The winner is: {winner}")
    return False

def handle(conn):

    while True:
        try:
            print(f"[BOB] Waiting for message...")
            msg = receive_json(conn)
            
            if not msg:
                if alice_nonce == "":
                    print(f"[Bob] Alice ran away! I win by default!")
                # Client disconnected
                break
                
            match msg.get("type"):
                case "game-commitment":
                    handle_game_commitment(msg, conn)
                case "reveal-nonce":
                    handle_reveal_nonce(msg)
                case _:
                    print(f"[Bob] Unknown message type: {msg.get('type')}")

                
        except socket.timeout:
            print(f"[Bob] Timeout waiting for Alice's nonce. I win by default!")
            break


    conn.close()
    print(f"[Bob] game over. Connection closed.")

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print("[BOB] Waiting for Alice to arrive...")
        sleep(2)
        conn, addr = s.accept()
        print("[BOB] Alice has arrived.")
        message = {
            "type": "game",
        }
        send_json(conn, message)
        print("[BOB] Sent game start message to Alice.")
        handle(conn)
    
if __name__ == "__main__":
    main()