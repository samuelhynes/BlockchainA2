import sys
import json
import hashlib

class Blockchain:
    
    def __init__(self):
        self.blockchain = []
        self.pool = []
        self.genesis_block()
        self.confirmed_nonce = {}
        self.next_nonce = {} 
        
    def genesis_block(self):
        """Creates initial genesis block 
        """
        block = self.pending_block("0"*64)
        self.add_block(block)
        
    def pending_block(self, prev_hash=None):
        """Adds new JSON block onto blockchain

        Args:
            prev_hash (hash): hash of previous block
        """

        new_block = {
            "index": len(self.blockchain) + 1,
            "transactions": self.pool.copy(),
            "previous_hash": prev_hash or self.blockchain[-1]["current_hash"],
        }
        new_block["current_hash"] = self.calculate_hash(new_block)
        return new_block
        
    def calculate_hash(self, block):
        block_object: str = json.dumps(
            {k: block.get(k) for k in ["index", "transactions", "previous_hash"]},
            sort_keys=True, 
            indent=2,
            separators=(',', ': ')
        )
        block_string = block_object.encode()
        raw_hash = hashlib.sha256(block_string)
        hex_hash = raw_hash.hexdigest()
        return hex_hash
    
    def add_transaction(self, transaction):
        self.pool.append(transaction)
    
    def get_pool(self):
        return self.pool.copy()
    
    def get_blockchain(self):
        return self.blockchain
    
    def add_block(self, new_block):
        self.blockchain.append(new_block)
        for tx in new_block["transactions"]:
            sender = tx["sender"]
            if sender not in self.confirmed_nonce:
                self.confirmed_nonce[sender] = 0
            self.confirmed_nonce[sender] += 1
        self.pool = []
        
        
    def get_expected_nonce(self, sender):
        if sender not in self.confirmed_nonce:
            confirmed = 0
        else:
            confirmed = self.confirmed_nonce[sender]
            
        pooled = 0
        for item in self.pool:
            if item["sender"] == sender:
                pooled += 1
        
        return pooled + confirmed

    def decrement(self, sender):
        self.next_nonce[sender] -= 1
        

