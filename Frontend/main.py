from flask import Flask

app = Flask(__name__)

@app.route("/")
def forecast_page():
    return "Hello this is the forecast page"

if __name__ == "__main__":
    app.run()