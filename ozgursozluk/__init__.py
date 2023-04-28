from flask import Flask


__version__ = "0.4.1"
__author__ = "beucismis"
__source__ = "https://github.com/beucismis/ozgursozluk"
__description__ = "free alternative simple ekşi sözlük front-end"

app = Flask(__name__)
app.config.from_object("ozgursozluk.config")


import ozgursozluk.views
