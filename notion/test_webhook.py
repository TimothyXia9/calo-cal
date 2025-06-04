from flask import Flask, request


app = Flask(__name__)


@app.route("/webhook", methods=["POST"])
def handle_webhook():
    data = request.json
    print(f"Received webhook: {data}")
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
