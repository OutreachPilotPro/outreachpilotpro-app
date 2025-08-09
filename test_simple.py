from flask import Flask, render_template

app = Flask(__name__)

@app.route("/test")
def test():
    return "Test route works!"

@app.route("/gdpr")
def gdpr():
    return render_template("gdpr.html")

if __name__ == '__main__':
    app.run(port=5002, debug=True)
