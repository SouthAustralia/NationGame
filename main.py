import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__, static_folder='.')
CORS(app)

PORT = 8080
DATA_FILE = 'users.json'


# Utility functions
def read_users():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading {DATA_FILE}: {e}")
    return {}


def write_users(users):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(users, f, indent=2)
    except Exception as e:
        print(f"Error writing {DATA_FILE}: {e}")


# Serve index.html
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


# Register or update a nation as online
@app.route('/online', methods=['POST'])
def register_online():
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Missing nation name'}), 400

    users = read_users()
    data['lastSeen'] = int(datetime.now().timestamp() * 1000)
    users[name] = data
    write_users(users)

    online = [
        n for n, info in users.items()
        if info.get('lastSeen', 0) > int(datetime.now().timestamp() * 1000) -
        5 * 60 * 1000
    ]

    return jsonify({'success': True, 'online': online})


# List currently online nations
@app.route('/online', methods=['GET'])
def list_online():
    users = read_users()
    now = int(datetime.now().timestamp() * 1000)
    threshold = now - 5 * 60 * 1000
    online = [
        n for n, info in users.items() if info.get('lastSeen', 0) > threshold
    ]
    return jsonify({'online': online})


# Get inbox data for a specific nation
@app.route('/inbox/<name>', methods=['GET'])
def inbox(name):
    users = read_users()
    user_data = users.get(name)
    if not user_data:
        return jsonify({'error': 'Nation not found'}), 404
    return jsonify(user_data)


# Mark a nation as offline
@app.route('/offline', methods=['POST'])
def logoff():
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Missing nation name'}), 400

    users = read_users()
    if name in users:
        users[name]['lastSeen'] = 0
        write_users(users)
        return jsonify({'success': True})
    return jsonify({'error': 'Nation not found'}), 404


# Handle trade between nations
@app.route('/trade', methods=['POST'])
def trade():
    data = request.get_json()
    sender = data.get('nation')
    target = data.get('target')
    trade_data = data.get('tradeData')

    if not sender or not target or not trade_data:
        return jsonify({'error': 'Missing trade parameters'}), 400

    users = read_users()
    sender_data = users.get(sender)
    target_data = users.get(target)

    if not sender_data or not target_data:
        return jsonify({'error': 'Sender or target nation not found'}), 404

    # Apply trade: subtract from sender, add to target
    for key, value in trade_data.items():
        value = max(0, int(value))
        sender_data[key] = max(0, int(sender_data.get(key, 0)) - value)
        target_data[key] = int(target_data.get(key, 0)) + value

    sender_data['lastSeen'] = int(datetime.now().timestamp() * 1000)
    users[sender] = sender_data
    users[target] = target_data
    write_users(users)

    return jsonify({'success': True, 'updatedState': sender_data})


# Start the server
if __name__ == '__main__':
    print(f"🚀 Nation Trading Server running at http://localhost:{PORT}")
    app.run(port=PORT)
