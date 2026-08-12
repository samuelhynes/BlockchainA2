import sys
import time

class Consensus:
    
    def __init__(self):
        self.list_proposals = []
        self.collected_peers = 0
        self.expected_peers = set()
        self.received_peers = set()
        
    def reset(self):
        self.expected_peers.clear()
        self.received_peers.clear()
        self.list_proposals.clear()
        self.collected_peers = 0
    
    def mark_expected(self, peer_id):
        self.expected_peers.add(peer_id)
        
    def mark_received(self, peer_id):
        self.received_peers.add(peer_id)

    def missing_peers(self):
        return self.expected_peers - self.received_peers
        
    def add_proposal(self, block):
        self.list_proposals.append(block)
          
    def values_message(self, round, port):        
        msg = {
            "type": "values",
            "payload": [],
            "round": round,
            "from": port
        }
        for item in self.list_proposals:            
            new_block = {
                "index": item["index"],
                "transactions": item["transactions"],
                "previous_hash": item["previous_hash"],
                "current_hash": item["current_hash"]
            }
            msg["payload"].append(new_block)
        
        return msg
    
    def decide_block(self):
        self.one_trans()
        chosen_block = min(self.list_proposals, key=lambda b: b["current_hash"])
        return chosen_block
         
    def one_trans(self):
        has_transactions = any(item["transactions"] for item in self.list_proposals)

        if has_transactions:
            self.list_proposals = [
                item for item in self.list_proposals if item["transactions"]
            ]
    
    def add_received(self):
        self.collected_peers += 1 
        
    def check_existing(self, proposal):
        if proposal in self.list_proposals:
            return True
        return False
    
