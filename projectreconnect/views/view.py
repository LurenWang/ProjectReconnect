from flask import Blueprint, render_template, current_app, redirect, url_for, Markup, request, flash
from flask.ext.login import current_user, login_required, login_user, logout_user
from werkzeug import secure_filename
import os
import json
from projectreconnect.forms.signup import SignInForm, SignUpForm
from projectreconnect.controllers.forms import create_account, update_user_genome, run_match, get_match_results
from projectreconnect.models.model import User
from projectreconnect.core import parse23andme
from projectreconnect import app
import pdb

home_bp = Blueprint('home', __name__)

@home_bp.route('/', methods=['GET', 'POST'])
def home():
    if current_user.is_anonymous:
        if request.method == 'POST':
            form = SignInForm(request.form)
            if form.validate():
                user = User.query.filter_by(email=form.email.data).first()
                if not user:
                    flash('Email does not exist')
                    return render_template('home.html', form=form)
                if not user.check_password(form.password.data):
                    flash('Invalid password')
                    return render_template('home.html', form=form)
                login_user(user)
                return redirect(url_for('home.dashboard', uid=user.uid))
        return render_template('home.html', form=SignInForm())
    else:
        return redirect(url_for('home.dashboard', uid=current_user.uid))

@home_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_anonymous:
        if request.method == 'POST':
            form = SignUpForm(request.form)
            if form.validate():
                email_exist = User.query.filter_by(email=form.email.data).first()
                if email_exist:
                    form.email.errors.append('Email already taken')
                    return render_template('signup.html', form=form)
                user = create_account(form.name.data, form.age.data, form.email.data, form.password.data)
                login_user(user)
                #login_user(user, remember=True)
                return redirect(url_for('home.dashboard', uid=user.uid))
            else:
                return render_template('signup.html', form=form)
        return render_template('signup.html', form=SignUpForm())
    else:
        return redirect(url_for('home.home'))

@home_bp.route('/dashboard/<int:uid>')
@login_required
def dashboard(uid):
    if current_user.uid != uid:
        return redirect(url_for('home.home'))
    user = User.query.filter_by(uid=uid).first()
    return render_template('dashboard.html', user=user)

@home_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('home.home'))

@home_bp.route('/upload', methods=['POST'])
@login_required
def upload():
    file = request.files['file']
    if file and allowed_file(file.filename):
        import numpy
        import time
        pdb.set_trace()
        if os.path.splitext(file.filename)[1] == '.csv':
            datastring = parse23andme(file)
        else:
            datastring = file.readline().decode('ascii')
        reg_array = [int(string) for string in datastring]
        genome = numpy.array(reg_array)
        update_user_genome(genome)
        results = run_match(current_user)
        match_results = get_match_results(results)
        time.sleep(3)
        return json.dumps(match_results), 200, {'ContentType':'application/json'}
    else:
        abort(400)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']
