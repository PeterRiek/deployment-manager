from flask import Flask, request

app = Flask(__name__)

@app.route("/gh-hook", methods=["POST", "GET"])
def gh_hook():
    print(request)
    return "Ok", 200
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)
