from flask import Flask
import os

# Super simple app - NO DATABASE at all!
app = Flask(__name__)

@app.route('/')
def home():
    return {"status": "online", "message": "Local test working!"}

if __name__ == '__main__':
    port = 5000
    print(f"🚀 Starting on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)