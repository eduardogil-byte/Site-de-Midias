from flask import render_template
from app.controllers.post_controller import posts


def home():
    return render_template("index.html", posts=posts)