from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html',msg = 'default')

@app.route('/about')
def about():
    return '<h1> This is an about page <h1>'

@app.route('/games')
def games():
    return '<h1> This is games page<h1>'
