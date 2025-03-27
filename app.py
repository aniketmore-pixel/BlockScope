from flask import Flask, jsonify, request, render_template
import time
import hashlib
import json

app = Flask(__name__)

# Blockchain Class Definitions
class Block:
    def __init__(self, index, transactions, previous_hash, nonce=0):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions if isinstance(transactions, list) else [transactions]  # Ensure list
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.find_hash()

    def find_hash(self):
        """Generates SHA-256 hash of the block's contents."""
        block_data = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce
        }, sort_keys=True)
        return hashlib.sha256(block_data.encode()).hexdigest()

    def mine_block(self, difficulty):
        """Performs Proof-of-Work to find a valid hash."""
        while self.hash[:difficulty] != "0" * difficulty:
            self.nonce += 1
            self.hash = self.find_hash()


class Blockchain:
    def __init__(self, difficulty=3):
        self.chain = [self.create_genesis_block()]
        self.difficulty = difficulty

    def create_genesis_block(self):
        return Block(0, ["Genesis Block"], "0")

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, transactions):
        transactions = transactions if isinstance(transactions, list) else [transactions]  # Ensure list
        new_block = Block(len(self.chain), transactions, self.get_latest_block().hash)
        new_block.mine_block(self.difficulty)
        self.chain.append(new_block)

    def is_chain_valid(self):
        """Validates the blockchain's integrity."""
        for i in range(1, len(self.chain)):  # Start from block 1 (Genesis block is untouchable)
            prev_block = self.chain[i - 1]
            current_block = self.chain[i]

            # Recalculate the hash of the previous block
            recalculated_prev_hash = hashlib.sha256(json.dumps(prev_block.__dict__, sort_keys=True).encode()).hexdigest()

            # If the stored previous_hash doesn't match recalculated hash → Blockchain is tampered
            if current_block.previous_hash != recalculated_prev_hash:
                return False

        return True

    def tamper_block(self, index, new_transactions):
        """Tamper with a block and recalculate hashes."""
        if index <= 0 or index >= len(self.chain):
            return False, "Invalid block index!"

        self.chain[index].transactions = new_transactions
        self.chain[index].hash = self.chain[index].find_hash()

        # Recalculate hashes for all subsequent blocks
        for i in range(index + 1, len(self.chain)):
            self.chain[i].previous_hash = self.chain[i - 1].hash
            self.chain[i].hash = self.chain[i].find_hash()

        return True, f"Block {index} tampered successfully!"


    def reset_chain(self):
        """Resets the blockchain to its initial state with only the genesis block."""
        self.chain = [self.create_genesis_block()]


# Create a global blockchain instance
aniket_blockchain = Blockchain()

# Home Route
@app.route("/")
def index():
    return render_template("index.html")


# API to View Blockchain
@app.route("/get_chain", methods=["GET"])
def get_chain():
    chain_data = []
    for block in aniket_blockchain.chain:
        chain_data.append({
            "index": block.index,
            "timestamp": block.timestamp,
            "transactions": block.transactions,
            "previous_hash": block.previous_hash,
            "hash": block.hash,
            "nonce": block.nonce
        })
    return jsonify({"chain": chain_data})


# API to Add a New Block
@app.route("/add_block", methods=["POST"])
def add_block():
    data = request.get_json()
    transactions = data.get("transactions", [])
    aniket_blockchain.add_block(transactions)
    return jsonify({"message": "Block added successfully!"})


# API to Validate the Blockchain
@app.route('/validate_chain', methods=['GET'])
def validate_chain():
    is_valid = aniket_blockchain.is_chain_valid()
    return jsonify({'valid': is_valid})



# API to Tamper with Blockchain
@app.route('/tamper_block', methods=['POST'])
def tamper_block():
    data = request.get_json()
    index = data.get("index")
    new_transactions = data.get("transactions", [])

    success, message = aniket_blockchain.tamper_block(index, new_transactions)
    return jsonify({"message": message})


# API to Reset Blockchain
@app.route("/reset_chain", methods=["POST"])
def reset_chain():
    aniket_blockchain.reset_chain()
    return jsonify({"message": "Blockchain reset successfully!"})


if __name__ == "__main__":
    app.run(debug=True)
