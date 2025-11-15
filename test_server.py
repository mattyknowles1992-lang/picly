from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "Server is working!"

@app.route('/test')
def test():
    return {'status': 'ok', 'message': 'Flask is running'}

if __name__ == '__main__':
    print("Starting test server on http://localhost:5000")
    try:
        app.run(host='127.0.0.1', port=5000, threaded=True)
    except Exception as e:
        print(f"Error starting server: {e}")
        input("Press Enter to exit...")
