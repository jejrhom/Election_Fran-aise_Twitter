"""
Routes and views for the flask application.
"""

from datetime import datetime
from flask import *
from Election_France_Flask import app
from .backend import *
import requests

@app.route('/')
def home():
    if request.method == "GET":
        return render_template('Search.html')

@app.route('/results', methods=['GET', 'POST'])
def results():
        if request.method == "POST":
            name_candidat = request.form["name_candidat"]
            results = Election_France(name_candidat)
        return render_template("Search.html", results=results)
