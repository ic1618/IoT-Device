from flask import render_template,request,Blueprint, redirect, request, url_for
from webapp import login_manager

core = Blueprint('core',__name__)

@core.route('/')
def index():
    '''
    This is the home page view.
    '''
    return render_template('index.html')

@core.route('/info')
def info():
    '''
    Info page.
    '''
    return render_template('features.html')

class User:
    pass

@core.route('/login', methods=['GET', 'POST'])
def login():
    """
    LogIn page.
    """
    error = None

    if request.method == 'POST':

        if request.form['username'] != 'tbchip' or request.form['password'] != 'catalin':
            error = 'Invalid Credentials. Please try again.'
        else:
            load_user(User())
            return redirect(url_for('flow.flow_page'))

    return render_template('login.html', error=error)

@login_manager.user_loader
def load_user(user):
    # print(user)
    return user
