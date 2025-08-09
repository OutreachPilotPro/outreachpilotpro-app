from app_minimal import app
from flask import render_template

with app.app_context():
    try:
        result = render_template("login.html")
        print("Login template renders successfully!")
        print("First 100 characters:", result[:100])
    except Exception as e:
        print("Error rendering login template:", e)
