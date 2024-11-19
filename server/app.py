from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import json
import time
import threading

app = Flask(__name__)
socketio = SocketIO(app)

# Store VPS status data, using dictionary to store each node's data and join time
vps_status = {}
TIMEOUT = 10  # 10 seconds timeout

def check_timeout():
    """Check and remove timeout clients"""
    while True:
        current_time = time.time()
        to_remove = []
        
        for node_name, data in vps_status.items():
            if current_time - data['last_update'] > TIMEOUT:
                to_remove.append(node_name)
        
        if to_remove:
            for node_name in to_remove:
                del vps_status[node_name]
            socketio.emit('status_update', vps_status)
        
        time.sleep(5)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update_status', methods=['POST'])
def update_status():
    data = request.json
    node_name = data['node_name']
    if node_name not in vps_status:
        data['join_time'] = time.time()
    else:
        data['join_time'] = vps_status[node_name]['join_time']
    
    data['last_update'] = time.time()  # Add last update time
    vps_status[node_name] = data
    socketio.emit('status_update', vps_status)
    return jsonify({"status": "success"})

@app.route('/get_status')
def get_status():
    return jsonify(vps_status)

if __name__ == '__main__':
    # Start timeout check thread
    timeout_thread = threading.Thread(target=check_timeout, daemon=True)
    timeout_thread.start()
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
