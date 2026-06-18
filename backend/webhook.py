from flask import Flask, request

app = Flask(__name__)

@app.route('/webhook', methods=['GET'])
def verify():
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if token == 'mytoken123':
        return challenge
    return 'Invalid token', 403

@app.route('/webhook', methods=['POST'])
def receive():
    return 'OK', 200

if __name__ == '__main__':
    app.run(port=5000)