"""
Copyright prolog and class level copyright are included in this utility.
This file is intended for the development of comments.
The user can make changes to the text/prolog-text as appropriate.
This work is licensed under
a Creative Commons Attribution-ShareAlike 3.0 Unported License.
©Thorben, 2021
email: thorbendhaenenstd@gmail.com

"""
import time

from flask import Flask, render_template, session, redirect, url_for, flash, request
import Database
import Contact

app = Flask(__name__)

main = Database.Main()
app.secret_key = main.get_secret_code()

@app.route('/', methods=['GET', 'POST'])
def index():
  
    return render_template('index.html')

@app.route('/admin_overview', methods=['GET', 'POST'])
def admin_overview():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        if request.method == 'POST':
            if 'btn_delete_comment' in request.form:
                main.delete_row_by_id('comments',request.form['btn_delete_comment'])
                redirect(url_for('admin_overview'))
            else:
                comment = Database.Comment(request.form['comment'])
                comment.register_comment()
                redirect(url_for('admin_overview'))
        return render_template('admin_overview.html', comments=main.read_table('comments'))

@app.route('/business_plan', methods=['GET', 'POST'])
def business_plan():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        return render_template('business_plan.html')

@app.route('/financial_plan', methods=['GET', 'POST'])
def financial_plan():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        investments,minimum,maximum = [],0,0
        for row in main.read_table('investments'):
            row = list(row)
            minimum += int(row[3])
            maximum += int(row[4])
            row[3] = "{:,}".format(int(row[3]))
            row[4] = "{:,}".format(int(row[4]))
            investments.append(row)
        minimum = "{:,}".format(int(minimum))
        maximum = "{:,}".format(int(maximum))
        fixed_costs = []
        for row in main.read_table('fixed_costs'):
            row = list(row)
            row[4] = "{:,}".format(int(row[4]))
            fixed_costs.append(row)
        return render_template('financial_plan.html', investments=investments, minimum=minimum, maximum=maximum, costs=fixed_costs)

@app.route('/products', methods=['GET', 'POST'])
def products():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        return render_template('products.html')

@app.route("/contact_submission", methods=["GET", "POST"])
def contact_submission():
    if request.method == "POST":
        print(request.form)
        cform = Contact.contactForm()
        if cform.validate_on_submit():
            print(f"Name:{cform.name.data}, E-mail:{cform.email.data}, message: {cform.message.data}")
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        session['logged_in'] = False
        return render_template('login.html')
    elif request.method == 'POST':
        if main.verify_password(request.form['emaillogin'], request.form['passwordlogin']):
            session['logged_in'] = True
            session['current_user'] = request.form['emaillogin']
            return redirect(url_for('admin_overview'))
        else:
            return redirect(url_for('login'))


@app.route("/logout")
def logout():
    session['logged_in'] = False
    return redirect(url_for('index'))


@app.errorhandler(400)
def bad_request(e):
    e_friendly = "The server and client don't seem to have any manners"
    return render_template('error.html', e=e, e_friendly=e_friendly), 400


@app.errorhandler(403)
def forbidden(e):
    e_friendly = "a forbidden resource"
    return render_template('error.html', e=e, e_friendly=e_friendly), 403


@app.errorhandler(404)
def not_found(e):
    e_friendly = "chap, you made a mistake typing that URL"
    return render_template('error.html', e=e, e_friendly=e_friendly), 404


@app.errorhandler(410)
def gone(e):
    e_friendly = "The page existed but is deleted and sent to Valhalla for all eternity."
    return render_template('error.html', e=e, e_friendly=e_friendly), 410


@app.errorhandler(500)
def internal_server_error(e):
    e_friendly = "'server problems' To be overloaded or not to be overloaded. That's the question."
    return render_template('error.html', e=e, e_friendly=e_friendly), 500
