from flask import Flask, request

app = Flask(__name__)

@app.route("/gh-hook", methods=["POST", "GET"])
def gh_hook():
    print(request)
    return "Ok", 200
    
