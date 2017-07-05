from flask import Flask, abort, flash, redirect, render_template, request, \
    session, url_for
from flask_bcrypt import Bcrypt
from pytz import common_timezones
import re
from sqlalchemy import exc
from emailr.models import User, Event
from emailr.database import db_session, init_db
from emailr.settings.config import JOGGY_SECRET_KEY


def create_app(debug=False):
    app = Flask(__name__)
    bcrypt = Bcrypt(app)
    app.debug = debug

    # set up database
    init_db()

    # add your modules
    # app.register_module(frontend)

    app.config['DEBUG'] = False
    app.config['SECRET_KEY'] = JOGGY_SECRET_KEY

    # Load default config and override config from an environment variable
    # app.config.update(
    #     dict(
    #         DEBUG=False,
    #         SECRET_KEY=JOGGY_SECRET_KEY
    #         # USERNAME='admin',
    #         # PASSWORD='default'
    #         # SERVER_NAME='0.0.0.0:80'
    #     ))
    # app.config.from_envvar('EMAILR_SETTINGS', silent=True)

    return app, bcrypt


app, bcrypt = create_app(debug=True)


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


def day_int_to_text(weekday):
    # Given the integer of a weekday, return the datetime string.
    weekdays = ['Monday',
                'Tuesday',
                'Wednesday',
                'Thursday',
                'Friday',
                'Saturday',
                'Sunday']
    return weekdays[weekday]

app.jinja_env.globals.update(day_int_to_text=day_int_to_text)


@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def new_user():
    if request.method == 'GET':
        if not session['id']:
            return render_template('new_user.html',
                                   available_tz=common_timezones)
        else:
            flash('You are already logged in.')
            return redirect(url_for('show_events'))
    else:
        pattern = re.compile(
            r'[^ \t\n\r\f\v@]+@[^ \t\n\r\f\v@]+\.[^ \t\n\r\f\v@]+', re.UNICODE)
        email = str(request.form['e-mail']).lower().strip()
        if pattern.match(email) is None:
            flash("Sorry, {e} is not a valid email address.".format(e=email))
            return render_template('new_user.html',
                                   available_tz=common_timezones)
        password = request.form['password']
        if len(password) > 71 or len(password) < 6:
            flash("Passwords must be between 6 and 71 characters.")
            return render_template('new_user.html',
                                   available_tz=common_timezones)
        try:
            pwd_hash = bcrypt.generate_password_hash(
                request.form['password']).decode('utf-8')
            user = User(email, pwd_hash, request.form['timezone'])
            db_session.add(user)
            db_session.commit()
            session['id'] = user.id
            session['user_tz'] = user.timezone_str
            session['user_email'] = user.email
            return redirect(url_for('show_events'))
        except exc.IntegrityError as e:
            db_session.rollback()
            if str(e).find("UNIQUE constraint failed") > -1:
                e = 'That email address is already in use.'
            flash('Sorry, an error occurred when trying to create your '
                  'account.')
            flash('{e}'.format(e=e))
    return render_template('new_user.html', available_tz=common_timezones)


@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'GET':
            if not session['id']:
                return render_template('login.html')
            else:
                flash('You are already logged in.')
                return redirect(url_for('show_events'))
        else:
            try:
                email = str(request.form['e-mail']).lower().strip()
                user = db_session.query(User).filter_by(email=email).one()
            except:
                flash("Email and password do not match.")
                raise ValueError("email entered doesn't exist")
            if not bcrypt.check_password_hash(user.pwd_hash, request.form[
                'password']):
                # password hash doesn't match database hash
                flash("Email and password do not match.")
                raise ValueError("wrong password entered")
            session['user_email'] = user.email
            session['user_tz'] = user.timezone_str
            session['id'] = user.id
            return redirect(url_for('show_events'))
    except:
        return render_template('login.html')


@app.route('/logout', methods=['GET'])
def logout():
    session['id'] = None
    session['user_email'] = None
    session['user_tz'] = None
    return redirect(url_for('home'))


highlight_id = None


@app.route('/settings')
def settings():
    if session['id'] is not None:
        user = db_session.query(User).filter_by(id=session[
            'id']).one()
        return render_template('settings.html', user=user)
    else:
        # abort(401)
        return redirect(url_for('login'))


@app.route('/reminders')
def show_events():
    if session['id'] is not None:
        global highlight_id
        to_highlight = highlight_id
        highlight_id = None
        events = db_session.query(Event).filter_by(user_id=session[
            'id']).order_by(Event.local_weekday, Event.local_time)
        return render_template('show_events.html',
                               events=events, to_highlight=to_highlight,
                               current_user=session['id'],
                               user_tz=session['user_tz'],
                               user_email=session['user_email'])
    else:
        # abort(401)
        return redirect(url_for('login'))


@app.route('/add', methods=['POST'])
def add_event():
    new_event = Event(int(request.form['weekday']), int(request.form[ 'hour']),
                      int(request.form['minute']), request.form['subject'],
                      session['user_tz'], session['id'])
    db_session.add(new_event)
    db_session.commit()
    global highlight_id
    highlight_id = new_event.id
    return redirect(url_for('show_events'))


@app.route('/delete', methods=['POST'])
def delete_event():
    delete_id = int(request.form['event_to_delete'])
    db_session.query(Event).filter_by(id=delete_id).delete()
    db_session.commit()
    flash("Your reminder was deleted.")
    return redirect(url_for('show_events'))


if __name__ == "__main__":
    app.run()