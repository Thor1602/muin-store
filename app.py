"""
Copyright prolog and class level copyright are included in this utility.
This file is intended for the development of comments.
The user can make changes to the text/prolog-text as appropriate.
This work is licensed under
a Creative Commons Attribution-ShareAlike 3.0 Unported License.
©Thorben, 2021
email: thorbendhaenenstd@gmail.com

TODO add file handler cloud
TODO add kakao alert messaging
TODO add email alert messaging
TODO add editing list for product, ingredient, recipe, etc
"""
import os
import pathlib
import random

from flask import Flask, render_template, session, redirect, url_for, flash, request, abort
from flask_babel import Babel, gettext, ngettext, lazy_gettext
from flask_mail import Mail, Message

import Database
import Contact

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app = Flask(__name__)
main = Database.Main()
app.secret_key = main.get_secret_code()
app.config['UPLOAD_FOLDER_INVOICES_SUPPLIER'] = pathlib.Path().resolve().__str__() + '/static/invoices/supplier'
app.config['UPLOAD_FOLDER_INVOICES_CUSTOMER'] = pathlib.Path().resolve().__str__() + '/static/invoices/customer'
app.config['BABEL_DEFAULT_LOCALE'] = 'ko'
app.config['LANGUAGES'] = ('ko', 'en')
app.config.update(dict(
    DEBUG = True,
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = 587,
    MAIL_USE_TLS = True,
    MAIL_USE_SSL = False,
    MAIL_USERNAME = 'thorbendhaenenstd@gmail.com',
    MAIL_PASSWORD = 'ejkprlxysssymdgc',
))

babel = Babel(app)
mail = Mail(app)

# app.config['UPLOAD_FOLDER_INVOICES_SUPPLIER'] = pathlib.Path().resolve().__str__() + '\\static\\invoices\\supplier'
# app.config['UPLOAD_FOLDER_INVOICES_CUSTOMER'] = pathlib.Path().resolve().__str__() + '\\static\\invoices\\customer'
# app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

nav_menu_admin = {'/admin_overview': 'Overview', '/business_plan': 'Business Plan', '/financial_plan': 'Financial Plan',
                  '/products': 'Products', '/recipes': 'Recipes', '/cost_calculation': 'Cost Calculation',
                  '/invoices': 'Invoices'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# BABEL CONFIG
@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'])

# PUBLIC
@app.route('/', methods=['GET', 'POST'])
def index():
    api_kakao_js = main.get_kakao_api_js()
    title = lazy_gettext('I like cake')
    # <b>{{ gettext('Free Trial') }}</b>  use _() as a shortcut for gettext().

    return render_template('index.html', api_kakao_js=api_kakao_js)


@app.route("/contact_submission", methods=["GET", "POST"])
def contact_submission():
    if request.method == "POST":
        # msg.recipients = ["rlatnals3020@naver.com"]
        admin_msg = Message("Coup De Foudre: Customer Contact Submit Website",
                            sender="from@example.com",
                            recipients=["to@example.com"])
        admin_msg.recipients = ["rlatnals3020@naver.com"]
        admin_msg.html = f"<b>Hello Sumin. {request.form['name']} contacted us on our website. Can you reply to this person? Info:<br>Name: {request.form['name']}<br>Address: {request.form['address']}<br>Phone: {request.form['phone']}<br>Email: {request.form['email']}<br>Subject: {request.form['subject']}<br>Message: {request.form['message']}</b>"
        mail.send(admin_msg)
        # cust_msg = Message("Coup De Foudre Customer Service",
        #                    sender="from@example.com",
        #                    recipients=["to@example.com"])
        # cust_msg.recipients = ["thorbendhaenenstd@gmail.com"]
        # cust_msg.html = f"<b>Thank you for contacting us, {request.form['name']}. We will reply ASAP.</b>"
        # cust_msg.send(cust_msg)
        # cform = Contact.contactForm()
        # if cform.validate_on_submit():
        #     print(f"Name:{cform.name.data}, E-mail:{cform.email.data}, message: {cform.message.data}")
    return redirect(url_for('index'))


# ADMIN
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
        return render_template('admin_overview.html', comments=main.read_table('comments'),
                               nav_menu_admin=nav_menu_admin)


@app.route('/business_plan', methods=['GET', 'POST'])
def business_plan():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        return render_template('business_plan.html', nav_menu_admin=nav_menu_admin)


@app.route('/cost_calculation', methods=['GET', 'POST'])
def cost_calculation():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        if request.method == 'POST':
            if 'ingredients_add_button' in request.form:
                ingredient = Database.Ingredients(request.form['english'], request.form['korean'])
                ingredient.register_ingredient()
            elif 'packaging_add_button' in request.form:
                packaging = Database.Packaging(request.form['english'], request.form['korean'])
                packaging.register()
            elif 'product_add_button' in request.form:
                product = Database.Products(request.form['english'], request.form['korean'],
                                            request.form['weight_in_gram_per_product'], request.form['unit'], request.form['image'])
                product.register()
            elif 'price_ingredient_add_button' in request.form:
                if request.form['date'] == '':
                    date = None
                else:
                    date = request.form['date']
                price_ingredient = Database.PricesIngredients(request.form['ingredientid'], request.form['price'],
                                                              request.form['weight_in_gram'], date)
                price_ingredient.register()
            elif 'price_packaging_add_button' in request.form:
                if request.form['date'] == '':
                    date = None
                else:
                    date = request.form['date']
                packaging_price = Database.PricesPackaging(request.form['packagingid'], request.form['price_per_unit'],
                                                           date)
                packaging_price.register()
            elif 'recipe_add_button' in request.form:
                for item in request.form:
                    if 'packagingid_' in item:
                        packaging_recipe = Database.PackagingProduct(request.form['productid'], request.form[item])
                        packaging_recipe.register()
                    elif 'ingredientid_' in item:
                        weight_in_gram = 'weight_in_gram_' + item.replace('ingredientid_', '')
                        ingredient_recipe = Database.IngredientProduct(request.form['productid'], request.form[item],
                                                                       request.form[weight_in_gram])
                        ingredient_recipe.register()
        ingredients = main.read_table('ingredients')
        products = main.read_table('products')
        packaging = main.read_table('packaging')
        return render_template('cost_calculation.html', nav_menu_admin=nav_menu_admin, packaging=packaging,
                               ingredients=ingredients, products=products)


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
                variable_cost = Database.VariableCost(request.form['productid'], request.form['variable_cost'],
                                                      request.form['selling_price_lv'], request.form['criteria_lv'],
                                                      request.form['selling_price_mv'], request.form['criteria_mv'],
                                                      request.form['selling_price_hv'], request.form['criteria_hv'],
                                                      request.form['work_time_min'],
                                                      request.form['estimated_items'])
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
        variable_costs_edit = main.read_table('variable_costs')
        products = main.read_table('products')
        variable_costs_edit_col = main.show_columns('variable_costs')
        variable_costs = main.fetch_variable_costs()[0]
        variable_costs_columns = main.fetch_variable_costs()[1]
        variable_costs_prefilled_input = ('', '','>=', '', '>=', '', '>=', '', '','', '')
        net_profit = {}
        for row in variable_costs:
            net_profit[row[2]] = [row[4], int(row[4] / 1.1), int((row[4] / 1.1) - row[3]), row[12], row[3]]

        return render_template('financial_plan.html', investments=investments, fixed_costs=fixed_costs, total=total,
                               variable_costs=variable_costs, variable_costs_columns=variable_costs_columns,
                               net_profit=net_profit, variable_costs_prefilled_input=variable_costs_prefilled_input,
                               nav_menu_admin=nav_menu_admin,variable_costs_edit_col=variable_costs_edit_col,variable_costs_edit=variable_costs_edit,products=products)


@app.route('/invoices', methods=['GET', 'POST'])
def invoices():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        if request.method == 'POST':
            print(request.form)
            if 'invoice_supplier_add_button' in request.form:
                if 'file' not in request.files:
                    return redirect(request.url)
                file = request.files['file']
                if file.filename == '':
                    return redirect(request.url)
                if file and allowed_file(file.filename):
                    filename = request.form['supplier_name'] + "_" + request.form['invoice_date'].replace('-',
                                                                                                          '') + f"_{random.randint(1, 100)}." + \
                               file.filename.rsplit('.', 1)[1].lower()
                    file.save(os.path.join(app.config['UPLOAD_FOLDER_INVOICES_SUPPLIER'], filename))
                    Database.InvoicesSupplier(file=filename, type=request.form['type'],
                                              payment_amount=request.form['payment_amount'],
                                              payment_method=request.form['payment_method'],
                                              supplier_name=request.form['supplier_name'],
                                              invoice_date=request.form['invoice_date']).register()
                    return redirect(url_for('invoices'))
            elif 'invoice_customer_add_button' in request.form:
                if 'file' not in request.files:
                    return redirect(request.url)
                file = request.files['file']
                if file.filename == '':
                    return redirect(request.url)
                if file and allowed_file(file.filename):
                    filename = request.form['customer_name'] + "_" + request.form['invoice_date'].replace('-',
                                                                                                          '') + f"_{random.randint(1, 100)}." + \
                               file.filename.rsplit('.', 1)[1].lower()
                    file.save(os.path.join(app.config['UPLOAD_FOLDER_INVOICES_CUSTOMER'], filename))
                    location = os.path.join(app.config['UPLOAD_FOLDER_INVOICES_CUSTOMER'], filename)
                    flash(location)
                    Database.InvoicesCustomer(file=filename, type=request.form['type'],
                                              payment_amount=request.form['payment_amount'],
                                              payment_method=request.form['payment_method'],
                                              customer_name=request.form['customer_name'],
                                              invoice_date=request.form['invoice_date']).register()
                    return redirect(url_for('invoices'))

        # invoices = main.read_table('invoices')
        invoices_customer = main.read_table('invoices_customers')
        invoices_supplier = main.read_table('invoices_suppliers')
        invoices_supplier_columns = main.show_columns('invoices_suppliers')
        invoices_customer_columns = main.show_columns('invoices_customers')
        return render_template('invoices.html', nav_menu_admin=nav_menu_admin, invoices_supplier=invoices_supplier,
                               invoices_customer=invoices_customer, invoices_supplier_columns=invoices_supplier_columns,
                               invoices_customer_columns=invoices_customer_columns)


@app.route('/products', methods=['GET', 'POST'])
def products():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        return render_template('products.html', nav_menu_admin=nav_menu_admin)


@app.route('/recipes', methods=['GET', 'POST'])
def recipes():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        if request.method == 'POST':
            if 'btn_edit_recipe' in request.form:
                data = request.form['btn_edit_recipe'].split(',')
                ingredient = Database.IngredientProduct(data[1], data[2], request.form['weight'])
                ingredient.update(data[0])
            elif 'btn_delete_recipe' in request.form:
                main.delete_row_by_id('ingredientproduct', request.form['btn_delete_recipe'])

        ingredients = main.read_table('ingredients')
        products = main.read_table('products')
        recipes = main.read_table('ingredientproduct')
        return render_template('recipes.html', nav_menu_admin=nav_menu_admin, recipes=recipes, ingredients=ingredients,
                               products=products)


# LOGIN LOGOUT
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


# ERROR HANDLING
@app.errorhandler(400)
def bad_request(e):
    e_friendly = "The server and client don't seem to have any manners"
    return render_template('error.html', e=e, e_friendly=e_friendly, nav_menu_admin=nav_menu_admin), 400


@app.errorhandler(403)
def forbidden(e):
    e_friendly = "a forbidden resource"
    return render_template('error.html', e=e, e_friendly=e_friendly, nav_menu_admin=nav_menu_admin), 403


@app.errorhandler(404)
def not_found(e):
    e_friendly = "chap, you made a mistake typing that URL"
    return render_template('error.html', e=e, e_friendly=e_friendly, nav_menu_admin=nav_menu_admin), 404


@app.errorhandler(410)
def gone(e):
    e_friendly = "The page existed but is deleted and sent to Valhalla for all eternity."
    return render_template('error.html', e=e, e_friendly=e_friendly, nav_menu_admin=nav_menu_admin), 410


@app.errorhandler(500)
def internal_server_error(e):
    e_friendly = "'server problems' To be overloaded or not to be overloaded. That's the question."
    return render_template('error.html', e=e, e_friendly=e_friendly, nav_menu_admin=nav_menu_admin), 500
