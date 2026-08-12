import json
from nacl.signing import SigningKey

# 1. Generate a new Ed25519 key pair
signing_key = SigningKey.generate()
verify_key = signing_key.verify_key

# 2. Build transaction payload
sender = verify_key.encode().hex()
message = "First Transaction"
nonce = 0

tx_payload = {
    "sender": sender,
    "message": message,
    "nonce": nonce
}

# 3. Serialize and sign the transaction
tx_bytes = json.dumps(tx_payload, sort_keys=True).encode('utf-8')
signature = signing_key.sign(tx_bytes).signature.hex()

# 4. Final transaction dictionary
tx_payload["signature"] = signature
full_tx = {
    "type": "transaction",
    "payload": tx_payload
}

# Output
print("✅ Transaction ready to send:")
print(json.dumps(full_tx, indent=2))

# Optional: print keys if needed later
print("\n🔑 Save this sender/private key pair for future use:")
print(f"Sender (Public Key): {sender}")
print(f"Private Key (hex): {signing_key.encode().hex()}")