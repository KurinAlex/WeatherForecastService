from flask import Flask
from flask import request
from flask import render_template

app = Flask(__name__)

@app.route("/")
def forecast_page():
    return render_template("home.html")

@app.route("/graphic")
def graphic_page():
    country = request.args.get("country")
    start = request.args.get("start")
    end = request.args.get("end")
    return render_template("graphic.html", country=country, start=start, end=end)


if __name__ == "__main__":
    app.run(port = 5001)