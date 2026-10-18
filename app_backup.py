from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/menu")
def menu():
    return render_template("menu.html")


@app.route("/cart")
def cart():
    return render_template("cart.html")

@app.route("/order")
def order():
    return render_template("order.html")

@app.route("/order-success")
def order_success():
    return render_template("order_success.html")

if __name__ == "__main__":
    app.run(debug=True)