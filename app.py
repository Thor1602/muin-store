"""
Copyright prolog and class level copyright are included in this utility.
This file is intended for the development of comments.
The user can make changes to the text/prolog-text as appropriate.
This work is licensed under
a Creative Commons Attribution-ShareAlike 3.0 Unported License.
©Thorben, 2021
email: thorbendhaenenstd@gmail.com

"""
import os
import time

from flask import Flask, render_template, session, redirect, url_for, flash, request, abort
import Database
import Contact

app = Flask(__name__)

main = Database.Main()
app.secret_key = main.get_secret_code()


# app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

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
                main.delete_row_by_id('comments', request.form['btn_delete_comment'])
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
        if request.method == "POST":
            if 'fixed_cost_edit_button' in request.form or 'fixed_cost_add_button' in request.form:
                fixed_cost = Database.FixedCost(request.form['english'], request.form['korean'],
                                                request.form['cost_per_month'], request.form['one_time_cost'],
                                                request.form['period'])
                if 'fixed_cost_add_button' in request.form:
                    fixed_cost.register_cost()
                elif 'fixed_cost_edit_button' in request.form:
                    fixed_cost.update_cost(request.form['fixed_cost_edit_button'])
            elif 'investment_edit_button' in request.form or 'investment_add_button' in request.form:

                investment = Database.Investment(request.form['english'], request.form['korean'],
                                                 request.form['min_price'], request.form['max_price'])
                if 'investment_add_button' in request.form:
                    investment.register_investment()
                elif 'investment_edit_button' in request.form:
                    investment.update_investment(request.form['investment_edit_button'])
            elif 'variable_cost_edit_button' in request.form or 'variable_cost_add_button' in request.form:
                variable_cost = Database.VariableCost(request.form['english'], request.form['korean'],
                                                      request.form['variable_cost'], request.form['selling_price_lv'],
                                                      request.form['criteria_lv'], request.form['selling_price_mv'],
                                                      request.form['criteria_mv'], request.form['selling_price_hv'],
                                                      request.form['criteria_hv'], request.form['unit'],
                                                      request.form['work_time_min'], request.form['image'])
                if 'variable_cost_add_button' in request.form:
                    variable_cost.register_cost()
                elif 'variable_cost_edit_button' in request.form:
                    variable_cost.update_cost(request.form['variable_cost_edit_button'])

            elif 'btn_delete_fixed_cost' in request.form:
                main.delete_row_by_id('fixed_costs', request.form['btn_delete_fixed_cost'])
            elif 'btn_delete_investment' in request.form:
                main.delete_row_by_id('investments', int(request.form['btn_delete_investment']))
            elif 'btn_delete_variable_cost' in request.form:
                main.delete_row_by_id('variable_costs', request.form['btn_delete_variable_cost'])
            else:
                abort(500)
        total = {'minimum': 0, 'maximum': 0, 'total_cost': 0}
        investments = []
        for row in main.read_table('investments'):
            row = list(row)
            total['minimum'] += int(row[3])
            total['maximum'] += int(row[4])
            investments.append(row)
        fixed_costs = []
        for row in main.read_table('fixed_costs'):
            row = [row[0], row[1], row[2], row[4], row[5], row[6]]
            total['total_cost'] += row[3]
            fixed_costs.append(row)
        variable_costs = main.read_table('variable_costs')
        variable_costs_columns = main.show_columns('variable_costs')
        variable_costs_prefilled_input = ('','','','','>=','','>=','','>=','','','.jpg')
        net_profit ={}
        for row in variable_costs:
            net_profit[row[2]]=[row[4], int(row[4]/1.1), int((row[4]/1.1)-row[3])]

        return render_template('financial_plan.html', investments=investments, fixed_costs=fixed_costs, total=total,
                               variable_costs=variable_costs, variable_costs_columns=variable_costs_columns,net_profit=net_profit,variable_costs_prefilled_input=variable_costs_prefilled_input)


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
