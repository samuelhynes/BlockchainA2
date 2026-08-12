import sys
import threading
import json
import hashlib
import socket
import math
import struct
import time
from queue import Queue, Empty
from transaction import Transaction
from values import Values
from blockchain import Blockchain
from consensus import Consensus
from datetime import datetime


MESSAGE_LENGTH = 65535


class Node:
    def __init__(self, args):
        self.command_line_args = args
        self.host = "127.0.0.1"
        self.peers = []
        
        self.blockchain = Blockchain()
        self.con = Consensus()
        self.outgoing_queues = {}
        self.values_received = False
        self.failed_nodes = 0
        self.consensus = False
        self.shutdown_event = threading.Event()  
        self.active_sockets = [] 
        
        self.round = 1
        self.failed_consensus = False

        self.total_expected_peers = len(self.peers)
        self.total_connected_peers = 0
        
        self.blockchain_lock = threading.Lock()
        self.proposal_lock = threading.Lock()
        self.consensus_lock = threading.Lock()
        
    def run(self):
        """Main function that starts program setup."""
        self.parse_args(self.command_line_args)
        self.parse_node_list()
        self.set_f()
        self.start_server()

    def parse_args(self, args):
        """Parses command line arguments into the Node class."""
        try:
            self.port = int(args[0])
            self.file_name = args[1]
        except ValueError:
            sys.exit(1)

    def parse_node_list(self):
        """Parses the node list file containing the hostname and port of each peer."""
        try:
            with open(self.file_name, 'r') as file:
                for line in file:
                    peer = line.strip().split(":")
                    if len(peer) > 2:
                        sys.exit(1)
                    elif len(peer) < 2:
                        return
                    try:
                        peer[1] = int(peer[1])  
                    except ValueError:
                        sys.exit(1)
                    self.add_peer_node(peer)
        except FileNotFoundError:
            sys.exit(1)

    def add_peer_node(self, peer):
        """Adds hostname and port as a tuple into the peer list."""
        self.peers.append((peer[0], peer[1]))

    def set_f(self):
        """Sets the fault tolerance threshold."""
        self.f = math.ceil(len(self.peers) / 2) - 1
        if self.f < 0:
            self.f = 0

    def start_server(self):
        """Starts the server and listens for incoming connections."""

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.active_sockets.append(self.server_socket)
        self.start_threads()

        try:
            while True:
                try:
                    client_socket, client_add = self.server_socket.accept()
                    self.active_sockets.append(client_socket)
                    while self.total_connected_peers < self.total_expected_peers:
                        time.sleep(0.1)
                    threading.Thread(target=self.server_connection, args=(client_socket, client_add), daemon=True).start()
                    
                except Exception as e:
                    break
        finally:
            self.server_socket.close()

    def start_threads(self):
        """Starts all threads in the program."""
        threading.Thread(target=self.consensus_process, daemon=True).start()
        threading.Thread(target=self.crash_fault_tolerance, daemon=True).start()

        for peer in self.peers:
            self.outgoing_queues[peer[1]] = Queue()
            threading.Thread(target=self.peers_send_msg_thread, args=(peer,), daemon=True).start()
        
    def peers_send_msg_thread(self, peer):
        """Thread that sends messages and maintains connection to a given peer."""
        try:
            while not self.shutdown_event.is_set():
                try:
                    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client_socket.connect((peer[0], int(peer[1])))
                    self.active_sockets.append(client_socket)
                    break
                except Exception:
                    time.sleep(0.1)
            
            self.total_connected_peers += 1

            while not self.shutdown_event.is_set():
                try:
                    message = self.outgoing_queues[peer[1]].get()
                    if message is None:
                        break
                    body = json.dumps(message).encode('utf-8')
                    length = len(body)

                    if length > MESSAGE_LENGTH:
                        sys.exit(1)

                    header = struct.pack('>H', length)
                    client_socket.sendall(header + body)
                    
                except Empty:
                    continue
                except Exception as e:
                    break
                time.sleep(0.1)
        finally:
            client_socket.close()
            if client_socket in self.active_sockets:
                self.active_sockets.remove(client_socket)
        

    def server_connection(self, client_socket, address):
        try:
            while True:
                header = client_socket.recv(2)
                first_msg = self.parse_msg(header, client_socket)
                if not first_msg:
                    return
                
                threading.Thread(target=self.handle_msg, args=(first_msg,client_socket), daemon=True).start()          
                time.sleep(0.1)
                
        except Exception:
            pass
        finally:
            client_socket.close()
            if client_socket in self.active_sockets:
                self.active_sockets.remove(client_socket)       
                
                
    def handle_msg(self, dict, client_socket):
               
        if dict['type'] == "values":
            
            if self.round == dict["round"]:
                
                proposal = self.blockchain.pending_block()
                self.con.add_proposal(proposal)
                response_message = self.con.values_message(self.round, self.port)
                self.create_msg(client_socket, response_message)
                
                sender_port = dict["from"]
                self.con.mark_received(sender_port)
                
                msg = Values(dict)
                payloads = msg.get_payloads()
                with self.proposal_lock: 
                    for item in payloads:
                        self.con.add_proposal(item)
                    self.con.add_received()
            

            if not self.consensus:
                self.values_received = True
                                    
        elif dict['type'] == "transaction":
                        
            msg = Transaction(dict["payload"])
            with self.consensus_lock: 
                if "fwd" in dict:
                    client = False
                else:
                    client = True
                    dict["fwd"] = True
                    
                                
                if msg.validate(self.blockchain):
                    if client: 
                        for peer in self.peers:
                            self.outgoing_queues[peer[1]].put(dict.copy())
                    self.blockchain.add_transaction(msg.get_transaction())
                    self.print_transaction(dict)
                    response = True
                    
                else:
                    response = False
                    
            if client:    
                self.create_msg(client_socket, response)
                
                
    def create_msg(self, sock, response):
        """Creates and sends a message."""
        response_body = json.dumps(response).encode('utf-8')
        response_length = len(response_body)
        response_header = struct.pack('>H', response_length)
        sock.send(response_header + response_body)

    def parse_msg(self, header, sock):
        """Parses a received message."""
        if not header:
            return None
        if len(header) < 2:
            return None
        (length,) = struct.unpack('>H', header)
        body = b''
        while len(body) < length:
            chunk = sock.recv(length - len(body))
            if not chunk:
                break
            body += chunk
        try:
            return json.loads(body.decode('utf-8'))
        except json.JSONDecodeError:
            return None

    def consensus_process(self):
        """Manages the consensus process."""
        while not self.shutdown_event.is_set():
            if len(self.blockchain.get_pool()) > 0:
                with self.consensus_lock:
                    proposal = self.blockchain.pending_block()
                    self.con.add_proposal(proposal)
                    self.consensus = True
                    self.consensus_sending()
            elif self.values_received:
                with self.consensus_lock:
                    self.consensus = True
                    self.consensus_sending()
            time.sleep(0.1)

    
    def consensus_sending(self):
        """Handles sending consensus messages."""
        
        with self.proposal_lock:
            for peer in self.peers:
                peer_id = peer[1]
                self.con.mark_expected(peer_id)
                self.outgoing_queues[peer[1]].put(self.con.values_message(self.round, self.port))
                
        start_time = time.time()
        while time.time() - start_time < 2.0:
            if not self.con.missing_peers():
                break 
            time.sleep(0.05)
        
        for peer_id in self.con.missing_peers():
            self.failed_nodes += 1
            for peer in self.peers:
                if peer[1] == peer_id:
                    self.peers.remove(peer)
                    break
        
        time.sleep(0.01)
        
        if not self.failed_consensus:
            block = self.con.decide_block()
            with self.blockchain_lock:
                self.blockchain.add_block(block)
            self.print_new_block(block)
            self.reset_consensus()
        
    def reset_consensus(self):
        """Resets the consensus state."""
       
        self.con.reset()
        self.consensus = False
        self.values_received = False
        self.round += 1

    def crash_fault_tolerance(self):
        """Checks if the number of failed nodes exceeds the fault tolerance threshold."""
        while True:
            if self.failed_nodes > self.f:
                self.failed_consensus = True
            time.sleep(0.01)

    def print_transaction(self, transaction):
        """Prints a transaction to stdout."""
        if "fwd" in transaction:
            del transaction["fwd"]
        print(json.dumps(transaction, sort_keys=True, indent=2), flush=True)

    def print_new_block(self, block):
        """Prints a new block to stdout."""
        print(json.dumps(block, sort_keys=True, indent=2), flush=True)

    def close_all_sockets(self):
        """Closes all active sockets."""
        for sock in self.active_sockets:
            try:
                sock.close()
            except Exception as e:
                continue 
        self.active_sockets.clear()


if __name__ == "__main__":
    app = Node(sys.argv[1:])
    try:
        app.run()
    except KeyboardInterrupt:
        app.shutdown_event.set()
        app.close_all_sockets()