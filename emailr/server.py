from flask import Flask, abort, flash, redirect, render_template, request, \
    session, url_for
from pytz import common_timezones
from sqlalchemy import exc
from emailr.models import User, Event
from emailr.database import db_session, init_db
from datetime import date, timedelta

# create our little application :)
app = Flask(__name__)

init_db()


# Load default config and override config from an environment variable
app.config.update(
    dict(
        DEBUG=True,
        SECRET_KEY='development key',
        USERNAME='admin',
        PASSWORD='default'
    ))
app.config.from_envvar('EMAILR_SETTINGS', silent=True)


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


@app.route('/new_user', methods=['GET', 'POST'])
def new_user():
    if request.method == 'POST':
        try:
            user = User(request.form['e-mail'], request.form['timezone'])
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
        if not session['id']:
            session['id'] = request.form['id']
            user = db_session.query(User).filter_by(id=session['id']).one()
            session['user_email'] = user.email
            session['user_tz'] = user.timezone_str
            return redirect(url_for('show_events'))
        else:
            return redirect(url_for('show_events'))
    except:
        return render_template('login.html')


@app.route('/logout', methods=['GET'])
def logout():
    session['id'] = None
    session['user_email'] = None
    session['user_tz'] = None
    return render_template('login.html')


highlight_id = None


@app.route('/')
def show_events():
    if session['id'] is not None:
        global highlight_id
        to_highlight = highlight_id
        highlight_id = None
        events = db_session.query(Event).filter_by(user_id=session[
            'id']).order_by(Event.local_weekday, Event.local_time)
        # db_session.close()
        return render_template('show_events.html',
                               events=events, to_highlight=to_highlight,
                               current_user=session['id'],
                               user_tz=session['user_tz'],
                               user_email=session['user_email'])
    else:
        abort(401)
        # return render_template('login.html')


@app.route('/add', methods=['POST'])
def add_event():
    new_event = Event(int(request.form['weekday']), int(request.form[ 'hour']),
                      int(request.form['minute']), request.form['subject'],
                      session['user_tz'], session['id'])
    db_session.add(new_event)
    db_session.commit()
    global highlight_id
    highlight_id = new_event.id
    flash('Your reminder was created for {d}s at {t}'.format(
        d=day_int_to_text(new_event.local_weekday),
        t=new_event.local_time.strftime("%I:%M %p")))
    return redirect(url_for('show_events'))


@app.route('/delete', methods=['POST'])
def delete_event():
    delete_id = int(request.form['event_to_delete'])
    db_session.query(Event).filter_by(id=delete_id).delete()
    db_session.commit()
    flash("Your reminder was deleted.")
    return redirect(url_for('show_events'))
