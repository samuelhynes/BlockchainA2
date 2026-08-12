import subprocess
import socket
import time
import threading

NODE_A_PORT = 5001
NODE_B_PORT = 5002

def launch_node_a():
    return subprocess.Popen(["python3", "-u", "main.py", str(NODE_A_PORT), "peers.txt"],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

def launch_fake_node_b():
    """Simulates a slow node that connects but never replies."""
    def run():
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("127.0.0.1", NODE_B_PORT))
        server.listen()
        while True:
            client_sock, addr = server.accept()
            print(f"[Slow Node B] Accepted connection from {addr}")
            while True:
                try:
                    header = client_sock.recv(2)
                    if not header:
                        break
                    length = int.from_bytes(header, 'big')
                    payload = client_sock.recv(length).decode('utf-8')
                    print(f"[Slow Node B] Ignoring message: {payload}")
                    # Do NOT send anything back
                except Exception:
                    break
    thread = threading.Thread(target=run, daemon=True)
    thread.start()

def send_transaction_to_node_a():
    tx = {
        "type": "transaction",
        "payload": {
            "sender": "1d8924e0d86cac34cdc471418c3420329c319f8e4f72ba4fe9fa1162fddbebac",
            "message": "First Transaction",
            "nonce": 0,
            "signature": "79f608dd999f752e542542d09de207d7b3e438ca2544b5a6a9a2f11b26b1eb7616d603848533b10099268efed4f46dc9cd203d1a15be1d608e9ef841abd0e501"
        }
    }
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("127.0.0.1", NODE_A_PORT))
    body = json.dumps(tx).encode('utf-8')
    header = len(body).to_bytes(2, 'big')
    sock.sendall(header + body)
    sock.close()

if __name__ == "__main__":
    import json

    print("✅ Starting Slow Node B")
    launch_fake_node_b()
    time.sleep(1)

    print("✅ Launching Node A")
    
    node_a = subprocess.Popen(
        ["python3", "-u", "main.py", str(NODE_A_PORT), "peers.txt"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
        universal_newlines=True
    )
    
    # node_a = launch_node_a()
    time.sleep(4)  # Give it time to connect to slow peer and timeout

    # Send a transaction if desired (optional)
    send_transaction_to_node_a()

    print("⏳ Waiting for Node A to attempt consensus and timeout")
    time.sleep(5)

    node_a.terminate()
    print("✅ Node A terminated")

    print("📄 Output from Node A:")
    for line in node_a.stdout:
        print(line.strip())