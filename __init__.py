"""
The flask application package.
"""

from flask import Flask
app = Flask(__name__)

import Election_France_Flask.views
