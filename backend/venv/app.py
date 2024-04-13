from flask import Flask, request, jsonify, render_template, url_for
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect 
import requests

app = Flask(__name__)
CORS(app)
csrf = CSRFProtect(app)

@app.route('/twitter/info', methods=["POST"])
@csrf.exempt
def get_twitter_info():
    try:
        link = request.form.get("link")

        print(link)
        return jsonify({
            "status": "Valid",
            "link": link
        })
    
    except Exception as e:
        return jsonify({
            "status": "Invalid",
            "error": str(e)
        })
    
@app.route('/twitter/info', methods=["POST"])
@csrf.exempt
def get_resources():
    return jsonify({
        "temp"
    })