from flask import Flask, request, jsonify
import subprocess
import threading
import time
import sys

from flask_cors import CORS
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
CORS(app)
# Talisman(app, force_https=True)  # force_https can be set to True if you want to enforce HTTPS internally
# app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

# Variable to store the latest webhook request data
latest_request_data = None
data_lock = threading.Lock()  # Lock to handle thread-safety


# Webhook endpoint that accepts POST requests
@app.route('/webhook', methods=['POST'])
def webhook():
    global latest_request_data
    with data_lock:  # Ensure thread-safe access
        latest_request_data = request.data  # Storing the incoming request data
    return jsonify({"status": "success", "message": "Webhook received"}), 200


# API endpoint to get the latest webhook request body
@app.route('/latest', methods=['GET'])
def get_latest_request():
    global latest_request_data
    with data_lock:  # Ensure thread-safe access
        if latest_request_data:
            return latest_request_data
        else:
            return jsonify({"message": "No webhook data received yet"}), 404


# Function to expose the local server using Serveo and capture output
def expose_via_serveo(local_port=5000):
    print(f"Exposing local server on port {local_port} to the internet using Serveo...")
    # Adding '-o StrictHostKeyChecking=no' to bypass host key verification
    serveo_command = f"ssh -o StrictHostKeyChecking=no -R 80:localhost:{local_port} serveo.net"

    # Start the Serveo process and redirect output to capture the public URL
    process = subprocess.Popen(serveo_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Capture and print Serveo's output (including the public URL)
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(output.strip())  # Print the Serveo output (this will include the public URL)
    return process


# Function to run Flask app
def run_flask_app():
    app.run(debug=False, use_reloader=False, port=5000)  # Disable debugger and reloader


if __name__ == '__main__':
    app.run()
    # Start the Flask app in a separate thread
    # flask_thread = threading.Thread(target=run_flask_app)
    # flask_thread.start()
    #
    # # Give the Flask server time to start properly
    # time.sleep(1)  # Short delay to ensure server is running
    #
    # # Expose the Flask server using Serveo and print the public URL
    # serveo_process = expose_via_serveo(local_port=5000)
    #
    # # Wait for the Serveo process to run, handle manual shutdown
    # try:
    #     serveo_process.wait()
    # except KeyboardInterrupt:
    #     print("Shutting down Serveo...")
    #     serveo_process.terminate()
    #     flask_thread.join()
