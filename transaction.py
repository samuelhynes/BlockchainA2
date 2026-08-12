import json
import sys
import re
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

sender_valid = re.compile("^[a-f0-9]{64}$")
sig_valid = re.compile("^[a-fA-F0-9]{128}$")

class Transaction:
    def __init__(self, msg):   
        self.dict = msg
        self.type = "transaction"
        
        
    def validate(self, blockchain):
        self.parse()
        if (
            not self.field_checks()
            or not self.nonce_check(blockchain)
            or not self.signature_verification()
        ):
            return False
        return True
    
    def parse(self):
        self.sender = self.dict["sender"]
        self.message = self.dict["message"]
        self.nonce = self.dict["nonce"]
        self.signature = self.dict["signature"]
        
    def nonce_check(self, blockchain):
        expected_nonce = blockchain.get_expected_nonce(self.sender)
        if self.nonce == expected_nonce:
            return True
        return False

            
    def signature_verification(self):
        try:
            vk = VerifyKey(bytes.fromhex(self.sender))
            tx = {
                'sender': self.sender,
                'message': self.message,
                'nonce': self.nonce,
            }
            tx_bytes = self.serialise(tx)
            sig = bytes.fromhex(self.signature)

            vk.verify(tx_bytes, sig)
            return True

        except Exception as e:
            return False
        
    def field_checks(self):
        if not (
            isinstance(self.sender, str)
            and sender_valid.search(self.sender)
        ):
            return False
        
        if not (
            isinstance(self.message, str)
            and len(self.message.encode('utf-8')) <= 70
        ):
            return False
            
        try:
            nonce = int(self.nonce) 
        except ValueError:
            return False
    
        if not (
            isinstance(self.signature, str)
            and sig_valid.search(self.signature)
        ):
            return False
        
        return True
            
    def serialise(self,tx):
        return json.dumps(tx, sort_keys=True).encode('utf-8')
        
    def get_message(self):
        return self.message
    
    def get_type(self):
        return self.type
    
    def get_sender(self):
        return self.sender
    
    def get_nonce(self):
        return self.nonce
    
    def get_signature(self):
        return self.signature
    
    def get_transaction(self):
        return self.dict
    