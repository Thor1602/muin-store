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
"""
import datetime
import random
import string
from datetime import timedelta
import pytz
import qrcode

from flask import Flask, Blueprint, render_template, session, redirect, url_for, flash, request, abort, make_response, \
    jsonify, Response
from flask_mail import Mail, Message
import pdfkit
import googledrive_connector
import naver_setup
import os.path

import Database

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app = Flask(__name__)
main = Database.Main()
app.secret_key = main.get_setting_by_name('secret_key')[1]
app.config['DEFAULT_LOCALE'] = 'ko_KR'
mail_cred = main.get_setting_by_name('main_gmail')
app.config.update(dict(
    DEBUG=True,
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_USERNAME=mail_cred[0],
    MAIL_PASSWORD=mail_cred[1],
))

mail = Mail(app)

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

nav_menu_admin = {'/admin_overview': 'Overview',
                  '고객': {'/contact_inquiry': '연락처 문의', '/qr_info': 'QR 정보', '/large_order_price': '대량 주문 목록'},
                  '제품': {'/recipes': '레시피'
                                     '', '/products': '다 제품'},
                  '경리': {'/invoices': '송장', '/business_plan': '비즈니스 계획',
                         '/financial_plan': '재무 계획'},
                  '사이트 관리자': {'/translations': '번역', '/images': '이미지',
                              '/cost_calculation': '비용 계산 추가하기',
                              '/edit_cost_calculation': '비용 계산 편집하기',
                              '/cost_per_product': 'Cost Per Product',
                              '/print_ingredient_list': '성분 목록 인쇄하기'}}

menu_item_home = {'#hero': 'home_title', '#best-product': 'best_product_title_nav', '#about': 'about_title',
                  '#contact': 'contact_title', '#clients': 'suppliers_title'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.context_processor
def get_locale():
    session['is_homepage'] = False
    session_name = session.get("preferred_language", default='ko_KR')
    if '/login' not in request.url or '/logout' not in request.url:
        session['url'] = request.url
    web_translations = main.read_table('web_translations')
    korean_translation = {}
    english_translation = {}
    for x in web_translations:
        key = x[1]
        korean_translation[key] = x[2]
        english_translation[key] = x[3]
    if session_name == 'ko_KR':
        return dict(msgid=korean_translation, nav_menu_admin=nav_menu_admin, menu_item_home=menu_item_home)
    else:
        return dict(msgid=english_translation, nav_menu_admin=nav_menu_admin, menu_item_home=menu_item_home)


# -----------------------PUBLIC-----------------------
@app.route("/lang_<lang>", methods=['GET', 'POST'])
def set_language(lang):
    session["preferred_language"] = lang
    return redirect(session['url'])


@app.route("/", methods=['GET', 'POST'])
def index():
    session['is_homepage'] = True
    api_kakao_js = main.get_setting_by_name('kakaoAPI')[1]
    best_products = []
    for row in main.read_table('products'):
        if row[8] == True:
            row_list = list(row)
            if not os.path.exists(os.path.abspath("static/img/products") + "/" + row[5]):
                row_list[5] = "no-image-available.jpg"
            best_products.append(row_list)
    if request.method == "POST":
        # msg.recipients = ["rlatnals3020@naver.com"]
        admin_msg = Message("Coup De Foudre: 문의 주세요!",
                            sender="from@example.com",
                            recipients=["to@example.com"])
        admin_msg.recipients = ["thorbendhaenenstd@gmail.com"]
        message = f"<b>띵동! {request.form['name']}한테 메시지가 왔어요!! <br> 성명: {request.form['name']}<br>주소: {request.form['address']}<br>전화번호: {request.form['phone']}<br>이메일주소: {request.form['email']}<br>제목: {request.form['subject']}<br>주요 메시지: {request.form['message']} <br> 더보기: https://cdf.herokuapp.com/contact_inquiry</b>"
        admin_msg.html = message
        mail.send(admin_msg)
        naver_setup.send_message_admin(f"문의 주세요! ({request.form['phone']}) {request.form['name']}")
        naver_setup.send_message_admin("더보기: https://cdf.herokuapp.com/contact_inquiry")
        Database.Contact(name=request.form['name'], email=request.form['email'], address=request.form['address'],
                         phone=request.form['phone'], subject=request.form['subject'],
                         message=request.form['message']).register_contact_query()
    return render_template('index.html', api_kakao_js=api_kakao_js, products=best_products)


@app.route("/products", methods=['GET', 'POST'])
def products():
    products = []
    for row in main.read_table('products'):
        row_list = list(row)
        if not os.path.exists(os.path.abspath("static/img/products") + "/" + row[5]):
            row_list[5] = "no-image-available.jpg"
        products.append(row_list)
    return render_template('products.html', products=products)


@app.route("/privacy_policy", methods=['GET', 'POST'])
def privacy_policy():
    return render_template('privacy_policy.html')


@app.route("/register_membership", methods=['GET', 'POST'])
def add_membership():
    if request.method == "POST":
        if "get_verification" in request.form:
            if session.get('verification_code'):
                time_now = pytz.utc.localize(datetime.datetime.now() - timedelta(minutes=5))
                time_verification = session['verification_code'][1]
                if time_now > time_verification:
                    session.pop('verification_code')
            if not session.get('verification_code'):
                session['verification_code'] = (random.randint(100000, 999999), datetime.datetime.now())
            phone_number = request.form['phone_number']
            for char in string.punctuation:
                phone_number = phone_number.replace(char, '')
            phone_number = phone_number.replace(' ', '')
            if main.phone_number_exists(phone_number):
                return make_response(
                    jsonify({'message': 'Phone number: ' + phone_number + ' exists.', 'code': 'ERROR'}), 201)
            else:
                session['member_registration'] = {'first_name': request.form['first_name'],
                                                  'last_name': request.form['last_name'], 'phone_number': phone_number}
                naver_setup.send_notification_code(to_no=phone_number, code=session['verification_code'][0],
                                                   language=session["preferred_language"])
                return make_response(jsonify(
                    {'message': 'The verification code has been sent to ' + phone_number + ".", 'code': 'SUCCESS'}),
                    201)
        elif "check_verification" in request.form:
            if session.get('verification_code'):
                if request.form['verification_code'] == str(session['verification_code'][0]):
                    Database.Membership(session['member_registration']['first_name'],
                                        session['member_registration']['last_name'],
                                        session['member_registration']['phone_number'], points=2000).register()
                    session.pop('member_registration')
                    return make_response(jsonify({'message': 'Verification completed', 'code': 'SUCCESS'}), 201)
                else:
                    return make_response(
                        jsonify({'message': 'Verification error: The codes did not match', 'code': 'ERROR'}), 201)
            else:
                return make_response(jsonify({'message': 'Verification code can be expired.', 'code': 'ERROR'}), 201)

    return render_template("add_membership.html")


@app.route("/membership", methods=['GET', 'POST'])
def check_membership():
    membership_data = main.read_table('memberships')
    if request.method == "POST":
        if "verification_request" in request.form:
            if request.form['phone_number'] not in [x[1] for x in membership_data]:
                flash("Phone number is not registered yet.")
                redirect(url_for('add_membership'))
            elif session.get('verification_code'):
                if session['verification_code'][1] + datetime.timedelta(minutes=5) <= datetime.datetime.now():
                    session['verification_code'] = (random.randint(100000, 999999), datetime.datetime.now())
                    flash("Verification code expired. A new code has been sent.")
                    naver_setup.send_notification_code(to_no=request.form['phone_number'],
                                                       code=session['verification_code'][0],
                                                       language=session["preferred_language"])
                else:
                    flash("Verification code is not expired yet. The code has been resent.")
                    naver_setup.send_notification_code(to_no=request.form['phone_number'],
                                                       code=session['verification_code'][0],
                                                       language=session["preferred_language"])
            else:
                session['verification_code'] = (random.randint(100000, 999999), datetime.datetime.now())

        elif "verification_validation" in request.form:
            if session.get('verification_code'):
                if session['verification_code'][1] + datetime.timedelta(minutes=5) <= datetime.datetime.now():
                    flash("Verification code is not correct.")
                    redirect(url_for('check_membership'))

                    if session['verification_code'][1] == request.form['given_verification_code']:
                        flash("Verification code has been verified.")
                        redirect(url_for('check_membership'))
                else:
                    flash("Verification code expired. Send a new code. ")
            else:
                flash("Verification code is not created yet.")

        elif "request_membership_points" in request.form:
            if request.form["verification_code"] == session['verification_code'][0] and session['verification_code'][
                1] + datetime.timedelta(minutes=5) >= datetime.datetime.now():
                flash("Verification succeeded")
            else:
                if request.form["verification_code"] != session['verification_code'][0]:
                    flash("Verification failed: code doesn't match")
                elif session['verification_code'][1] + datetime.timedelta(minutes=5) <= datetime.datetime.now():
                    flash("Verification failed: code has expired. Try again.")
                else:
                    abort(500)
            redirect(url_for('add_membership'))
        redirect(url_for("add_membership"))
    return render_template("check_membership.html")


# -----------------------ADMIN-----------------------
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


@app.route('/cost_calculation', methods=['GET', 'POST'])
def cost_calculation():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        if request.method == 'POST':
            if 'ingredients_add_button' in request.form:
                ingredient = Database.Ingredients(request.form['english'], request.form['korean'], get_ingredientid=True)
                ingredientid = ingredient.register_ingredient()
                print(ingredientid)
                if request.form['date'] == '':
                    date = None
                else:
                    date = request.form['date']
                Database.PricesIngredients(ingredientid, request.form['price'],
                                           request.form['weight_in_gram'], date).register()

            elif 'packaging_add_button' in request.form:
                packaging = Database.Packaging(request.form['english'], request.form['korean'], get_packagingid=True)
                packagingid = packaging.register()
                if request.form['date'] == '':
                    date = None
                else:
                    date = request.form['date']
                packaging_price = Database.PricesPackaging(packagingid, request.form['price_per_unit'],
                                                           date)
                packaging_price.register()
            elif 'product_add_button' in request.form:
                if 'currently_selling' in request.form:
                    currently_selling = request.form['currently_selling'] == 'on'
                else:
                    currently_selling = False
                if 'best_product' in request.form:
                    best_product = request.form['best_product'] == 'on'
                else:
                    best_product = False
                Database.Products(request.form['english'], request.form['korean'],
                                            request.form['weight_in_gram_per_product'], request.form['unit'],
                                            request.form['image'], type=request.form['type'],
                                            currently_selling=currently_selling, best=best_product,
                                            Korean_description=request.form['Korean_description'],
                                            English_description=request.form['English_description'],
                                            QR=request.form['QR']).register()
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
        missing_prices_ingredients = main.missing_prices_ingredients()
        missing_prices_packaging = main.missing_prices_packaging()
        return render_template('cost_calculation.html', packaging=packaging,
                               ingredients=ingredients, products=products,missing_prices_packaging=missing_prices_packaging,missing_prices_ingredients=missing_prices_ingredients)


@app.route('/edit_cost_calculation', methods=['GET', 'POST'])
def edit_cost_calculation():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        if request.method == "POST":
            print(request.form)
            if 'products_edit_button' in request.form:
                if 'currently_selling' in request.form:
                    currently_selling = request.form['currently_selling'] == 'on'
                else:
                    currently_selling = False
                if 'best_product' in request.form:
                    best_product = request.form['best_product'] == 'on'
                else:
                    best_product = False
                Database.Products(english=request.form['english'], korean=request.form['korean'],
                                  weight_in_gram_per_product=request.form['weight'], unit=request.form['unit'],
                                  image=request.form['image'], type=request.form['type'],
                                  currently_selling=currently_selling, best=best_product,
                                  Korean_description=request.form['Korean_description'],
                                  English_description=request.form['English_description'],
                                  QR=request.form['QR']).update(
                    request.form['products_edit_button'])

        data_dictionary = {}
        data_dictionary['ingredients'] = main.read_table('ingredients')
        data_dictionary['products'] = main.read_table('products')
        data_dictionary['packaging'] = main.read_table('packaging')
        data_dictionary['prices_ingredients'] = main.read_table('prices_ingredients')
        data_dictionary['prices_packaging'] = main.read_table('prices_packaging')
        data_dictionary['packagingproduct'] = main.read_table('packagingproduct')
        data_dictionary['ingredientproduct'] = main.read_table('ingredientproduct')
        data_dictionary['ingredients_col'] = main.show_columns('ingredients')
        data_dictionary['products_col'] = main.show_columns('products')
        data_dictionary['packaging_col'] = main.show_columns('packaging')
        data_dictionary['prices_ingredients_col'] = main.show_columns('prices_ingredients')
        data_dictionary['prices_packaging_col'] = main.show_columns('prices_packaging')
        data_dictionary['packagingproduct_col'] = main.show_columns('packagingproduct')
        data_dictionary['ingredientproduct_col'] = main.show_columns('ingredientproduct')
        return render_template('edit_cost_calculation.html',
                               data_dictionary=data_dictionary)


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
        variable_costs_prefilled_input = ('', '', '>=', '', '>=', '', '>=', '', '', '', '')
        net_profit = {}
        for row in variable_costs:
            net_profit[row[2]] = [row[4], int(row[4] / 1.1), int((row[4] / 1.1) - row[3]), row[12], row[3]]

        return render_template('financial_plan.html', investments=investments, fixed_costs=fixed_costs, total=total,
                               variable_costs=variable_costs, variable_costs_columns=variable_costs_columns,
                               net_profit=net_profit, variable_costs_prefilled_input=variable_costs_prefilled_input,
                               variable_costs_edit_col=variable_costs_edit_col,
                               variable_costs_edit=variable_costs_edit, products=products)


@app.route('/invoices', methods=['GET', 'POST'])
def invoices():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        if request.method == 'POST':
            if 'invoice_supplier_add_button' in request.form:
                if 'file' not in request.files:
                    flash('No file part')
                    return redirect(request.url)
                files = request.files.getlist("file")
                for file in files:
                    if file.filename == '':
                        flash('File has no filename')
                        break
                    extension = file.filename.rsplit('.', 1)[1]
                    if request.form['invoice_date'] == "":
                        date = datetime.datetime.now().strftime("%Y-%m-%d")
                    else:
                        date = request.form['invoice_date']
                    file.filename = request.form['supplier_name'] + "_" + date + "." + extension
                    if file and allowed_file(file.filename):
                        googledrive_connector.upload_invoice(file)
                        Database.InvoicesSupplier(file=file.filename, type=request.form['type'],
                                                  payment_amount=request.form['payment_amount'],
                                                  payment_method=request.form['payment_method'],
                                                  supplier_name=request.form['supplier_name'],
                                                  invoice_date=date).register()
                        flash('File name: ' + file.filename + ' is uploaded.')
                    else:
                        flash('File name: ' + file.filename + ' is not allowed.')
                    return redirect(url_for('invoices'))
            elif 'invoice_customer_add_button' in request.form:
                if 'file' not in request.files:
                    flash('No file part')
                    return redirect(request.url)
                files = request.files.getlist("file")
                for file in files:
                    if file.filename == '':
                        flash('File has no filename')
                        break
                    extension = file.filename.rsplit('.', 1)[1]
                    if request.form['invoice_date'] == "":
                        date = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    else:
                        date = request.form['invoice_date']
                    file.filename = request.form['customer_name'] + "_" + date + "." + extension
                    if file and allowed_file(file.filename):
                        googledrive_connector.upload_invoice(file)
                        Database.InvoicesSupplier(file=file.filename, type=request.form['type'],
                                                  payment_amount=request.form['payment_amount'],
                                                  payment_method=request.form['payment_method'],
                                                  supplier_name=request.form['customer_name'],
                                                  invoice_date=date).register()
                        flash('File name: ' + file.filename + ' is uploaded.')
                    else:
                        flash('File name: ' + file.filename + ' is not allowed.')
                    return redirect(url_for('invoices'))
        invoices_customer = main.read_table('invoices_customers')
        invoices_supplier = main.read_table('invoices_suppliers')
        invoices_supplier_columns = main.show_columns('invoices_suppliers')
        invoices_customer_columns = main.show_columns('invoices_customers')
        return render_template('invoices.html', invoices_supplier=invoices_supplier,
                               invoices_customer=invoices_customer, invoices_supplier_columns=invoices_supplier_columns,
                               invoices_customer_columns=invoices_customer_columns)


@app.route('/images', methods=['GET', 'POST'])
def images():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        return render_template('images.html', cloud_images=[])


@app.route('/contact_inquiry', methods=['GET', 'POST'])
def contact_inquiry():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        contact_info = main.read_table('customer_contact_submission', order_desc="time")
        return render_template('contact_inquiry.html', contact_info=contact_info)


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
        return render_template('recipes.html', recipes=recipes, ingredients=ingredients,
                               products=products)


@app.route('/cost_per_product', methods=['GET', 'POST'])
def cost_per_product():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        data = {}
        data['ingredients'] = main.read_table('ingredients')
        data['packaging'] = main.read_table('packaging')
        data['packagingproduct'] = main.read_table('packagingproduct')
        data['products'] = main.read_table('products')
        data['ingredientproduct'] = main.read_table('ingredientproduct')
        data['ingredients_get_average'] = main.get_price('ingredients', get_average=True)
        data['ingredients_get_latest'] = main.get_price('ingredients', get_latest=True)
        data['packaging_get_average'] = main.get_price('packaging', get_average=True)
        data['packaging_get_latest'] = main.get_price('packaging', get_latest=True)
        data['total_average_packaging'] = {}
        for packagingproduct in data['packagingproduct']:
            if packagingproduct[2] in data['packaging_get_average']:
                product_id = packagingproduct[1]
                if product_id in data['total_average_packaging']:
                    data['total_average_packaging'][product_id] += round(
                        data['packaging_get_latest'][packagingproduct[2]], 2)
                else:
                    data['total_average_packaging'][product_id] = round(
                        data['packaging_get_latest'][packagingproduct[2]], 2)
        data['total_latest_packaging'] = {}
        for packagingproduct in data['packagingproduct']:
            if packagingproduct[2] in data['packaging_get_latest']:
                product_id = packagingproduct[1]
                if product_id in data['total_latest_packaging']:
                    data['total_latest_packaging'][product_id] += data['packaging_get_latest'][packagingproduct[2]]
                else:
                    data['total_latest_packaging'][product_id] = data['packaging_get_latest'][packagingproduct[2]]

        data['total_weight'] = {}
        for row in data['ingredientproduct']:
            if row[1] in data['total_weight']:
                data['total_weight'][row[1]] += row[3]
            else:
                data['total_weight'][row[1]] = row[3]
        data['total_average_ingredients'] = {}
        for ingredientproduct in data['ingredientproduct']:
            if ingredientproduct[2] in data['ingredients_get_average']:
                product_id = ingredientproduct[1]
                if product_id in data['total_average_ingredients']:
                    data['total_average_ingredients'][product_id] += round(ingredientproduct[3] * data['ingredients_get_average'][
                        ingredientproduct[2]],2)
                else:
                    data['total_average_ingredients'][product_id] = round(ingredientproduct[3] * data['ingredients_get_average'][
                        ingredientproduct[2]],2)
        data['total_latest_ingredients'] = {}
        for ingredientproduct in data['ingredientproduct']:
            if ingredientproduct[2] in data['ingredients_get_latest']:
                product_id = ingredientproduct[1]
                if product_id in data['total_latest_ingredients']:
                    data['total_latest_ingredients'][product_id] += round(ingredientproduct[3] * data['ingredients_get_latest'][
                        ingredientproduct[2]],2)
                else:
                    data['total_latest_ingredients'][product_id] = round(ingredientproduct[3] * data['ingredients_get_latest'][
                        ingredientproduct[2]],2)
        for product in data['products']:
            if product[0] not in data['total_latest_ingredients']:
                data['total_latest_ingredients'][product[0]] = 0
            if product[0] not in data['total_average_ingredients']:
                data['total_average_ingredients'][product[0]] = 0
            if product[0] not in data['total_weight']:
                data['total_weight'][product[0]] = 0
            if product[0] not in data['total_latest_packaging']:
                data['total_latest_packaging'][product[0]] = 0
            if product[0] not in data['total_average_packaging']:
                data['total_average_packaging'][product[0]] = 0
            if product[0] not in data['total_latest_ingredients']:
                data['total_latest_ingredients'][product[0]] = 0
        data['total_average_ingredients_per_unit'] = {}
        data['total_average'] = {}
        data['total_latest_ingredients_per_unit'] = {}
        data['total_latest'] = {}
        for product in data['products']:
            if data['total_average_ingredients'][product[0]] == 0:
                data['total_average_ingredients_per_unit'][product[0]] = 0
            else:
                data['total_average_ingredients_per_unit'][product[0]] = round(data['total_average_ingredients'][product[0]] / (data['total_weight'][product[0]] / product[3]),2)
            data['total_average'][product[0]] = round(data['total_average_ingredients_per_unit'][product[0]] + data['total_average_packaging'][product[0]],0)

            if data['total_latest_ingredients'][product[0]] == 0:
                data['total_latest_ingredients_per_unit'][product[0]] = 0
            else:
                data['total_latest_ingredients_per_unit'][product[0]] = round(data['total_latest_ingredients'][product[0]] / (data['total_weight'][product[0]] / product[3]),2)
            data['total_latest'][product[0]] = round(data['total_latest_ingredients_per_unit'][product[0]] + data['total_latest_packaging'][product[0]],0)
        return render_template('cost_per_product.html', data=data)


@app.route('/translations', methods=['GET', 'POST'])
def translations():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        web_translations_col = main.show_columns('web_translations')
        if request.method == 'POST':
            translation_object = Database.WebTranslations(request.form[web_translations_col[1]],
                                                          request.form[web_translations_col[2]],
                                                          request.form[web_translations_col[3]])
            if 'translation_modal_add_button' in request.form:
                translation_object.register()
            elif 'translation_modal_edit_button' in request.form:
                translation_object.update(request.form['translation_modal_edit_button'])
                global web_translations
                web_translations = main.read_table('web_translations')
        sorted_web_translations = main.read_table('web_translations', order_asc="msgid")
        return render_template('homepage_admin.html', web_translations=sorted_web_translations,
                               web_translations_col=web_translations_col)


@app.route('/qr_info', methods=['GET', 'POST'])
def qr_info():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        if request.method == 'POST':
            for key in request.form:
                if 'product_' in key:
                    img = qrcode.make(request.form[key])
                    img.save("/static/img/QR/" + request.form[key] + ".png")
            return render_template('qr_info.html')
        return render_template('qr_info.html')


@app.route('/large_orders_price', methods=['GET', 'POST'])
def large_orders_price():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        products = main.read_table('products')
        variable_costs = main.read_table('variable_costs')
        return render_template('large_orders_price.html', products=products,
                               variable_costs=variable_costs)


@app.route('/print_ingredient_list', methods=['GET', 'POST'])
def print_ingredient_list():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    else:
        data_dictionary = {}
        data_dictionary['ingredients'] = main.read_table('ingredients')
        data_dictionary['ingredients_col'] = main.show_columns('ingredients')
        data_dictionary['packaging'] = main.read_table('packaging')
        data_dictionary['packaging_col'] = main.show_columns('packaging')
        data_dictionary['length_ingredients'] = int(len(data_dictionary['ingredients']) / 2)
        data_dictionary['length_packaging'] = int(len(data_dictionary['packaging']) / 2)
        html = render_template('print_ingredient_list.html', data_dictionary=data_dictionary)
        return html


# LOGIN LOGOUT
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        flash('This is only for admins.')
        session['logged_in'] = False
        return render_template('login.html')
    elif request.method == 'POST':
        if main.verify_password(request.form['emaillogin'], request.form['passwordlogin']):
            session['logged_in'] = True
            session['current_user'] = request.form['emaillogin']
            flash('Logged in')
            return redirect(url_for('admin_overview'))
        else:
            return redirect(url_for('login'))


@app.route("/logout")
def logout():
    session['logged_in'] = False
    flash('This is only for admins.')
    return redirect(url_for('login'))


# ERROR HANDLING
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
    e_friendly = "'server problems' To be or not being overloaded. That's the question."
    return render_template('error.html', e=e, e_friendly=e_friendly), 500
