from flask import Flask
from flask import render_template

app = Flask(__name__)

@app.route("/")
def forecast_page():
    return render_template("home.html")

@app.route("/graphic")
def graphic_page():
    return render_template("graphic.html")


if __name__ == "__main__":
    app.run()