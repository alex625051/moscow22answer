from flask import Blueprint, render_template, jsonify, request


games1 = Blueprint('games1', __name__, template_folder='templates', static_folder='static')



@games1.route('/')
def index():
    return render_template('games1/index.html')

@games1.route('/snake/')
def snake():
    return render_template('games1/snake.html')

@games1.route('/helicopter/')
def helicopter():
    return render_template('games1/helicopter.html')

@games1.route('/bomberman/')
def bomberman():
    return render_template('games1/bomberman.html')

@games1.route('/frogger/')
def frogger():
    return render_template('games1/frogger.html')

@games1.route('/pong/')
def pong():
    return render_template('games1/pong.html')

@games1.route('/missile-command/')
def missile_command():
    return render_template('games1/missile-command.html')

@games1.route('/tetris/')
def tetris():
    return render_template('games1/tetris.html')

@games1.route('/sokoban/')
def sokoban():
    return render_template('games1/sokoban.html')

@games1.route('/gonki/')
def gonki():
    return render_template('games1/gonki.html')

@games1.route('/breakout/')
def breakout():
    return render_template('games1/breakout.html')