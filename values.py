from transaction import Transaction
import sys


class Values:
    def __init__(self, msg):
        self.dict = msg
        self.payload = []
        self.parse()
        
    def parse(self):
        payload = self.dict['payload']
        for block in payload:
            index = block["index"]
            transactions = block["transactions"]
            prev_hash = block["previous_hash"]
            current_hash = block["current_hash"]
            
            new_block = {
                "index": index,
                "transactions": transactions,
                "previous_hash": prev_hash,
                "current_hash": current_hash
            }
            self.payload.append(new_block)
        
    def get_payloads(self):
        return self.payload
        
        
    

    
    