"""
Copyright prolog and class level copyright are included in this utility.
This file is intended for the development of comments.
The user can make changes to the text/prolog-text as appropriate.
This work is licensed under
a Creative Commons Attribution-ShareAlike 3.0 Unported License.
©Thorben, 2021
email: cdfguri@gmail.com

TODO add file handler cloud
TODO add kakao alert messaging
TODO REGULARLY gmail app password, secret_key, postgres, admin
more info later
"""
from datetime import datetime as datetimelib
import logging
from os.path import exists

import qrcode

from flask import Flask, render_template, session, redirect, url_for, flash, request, abort, send_from_directory
from flask_mail import Mail, Message
from flask_compress import Compress

# from flask_debugtoolbar import DebugToolbarExtension

import flask_login
import googledrive_connector
import naver_setup
import os.path
import os
import Database
from InputForms import *
from functools import wraps
from flask_rq2 import RQ
import collections

# from secure import SecureHeaders

# secure_headers = SecureHeaders()

app = Flask(__name__)
main = Database.Main()

Database.open_connection()
mail_cred = main.get_setting_by_name('mail_cred_2')
encrypted_login_session = main.get_setting_by_name('logged_in_session')[0]
app.secret_key = main.get_setting_by_name('secret_key')[1]
redis_external_url = main.get_setting_by_name('redis_external_url')[1]
path_to_db_credentials = main.get_setting_by_name('path_to_db_credentials')[1]
Database.close_connection()
app.config['DEFAULT_LOCALE'] = 'ko_KR'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config.update(dict(
    DEBUG=True,
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_USERNAME=mail_cred[0],
    MAIL_PASSWORD=mail_cred[1],
),
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=600
)
if exists(
        'D:\\Users\\Thorben\\OneDrive - University of the People\\PycharmProjects\\bakery\\gitignore\\database_credentials.txt'):
    app.debug = True
else:
    app.debug = False

mail = Mail(app)
rq = RQ(app)
Compress(app)

# secure_headers = SecureHeaders()
# toolbar = DebugToolbarExtension(app)
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.session_protection = 'strong'

nav_menu_admin = {'/admin_overview': 'Overview',
                  '고객': {'/contact_inquiry': '연락처 문의', '/qr_info': 'QR 정보', '/large_order_price': '대량 주문 목록'},
                  '제품': {'/recipes': '레시피'
                                     '', '/products': '다 제품'},
                  '경리': {'/invoices': '송장', '/business_plan': '비즈니스 계획',
                         '/financial_plan': '재무 계획'},
                  '사이트 관리자': {'/translations': '번역', '/images': '이미지',
                              '/loss_calculator': '손실 계산기',
                              '/cost_calculation': '비용 계산 추가하기',
                              '/edit_cost_calculation': '비용 계산 편집하기',
                              '/cost_per_product': '제품당 비용',
                              '/print_ingredient_list': '성분 목록 인쇄하기'}}

menu_item_home = {'#hero': 'home_title', '#best-product': 'best_product_title_nav', '#about': 'about_title',
                  '#contact': 'contact_title', '#clients': 'suppliers_title'}
trusted_ip = ('127.0.0.1', '211.208.140.83')
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
# -----------------------LOGGING-----------------------

gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)


# app.logger.debug('This is a DEBUG log record.')
# app.logger.info('This is an INFO log record.')
# app.logger.warning('This is a WARNING log record.')
# app.logger.error('This is an ERROR log record.')
# app.logger.critical('This is a CRITICAL log record.')
# -----------------------BEFORE AFTER REQUEST-----------------------

def postgres_connection(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        Database.open_connection()
        value = func(*args, **kwargs)
        Database.close_connection()
        return value

    return wrapper


@app.before_request
def before_request():
    if not exists(path_to_db_credentials):
        if not request.is_secure:
            url = request.url.replace('http://', 'https://', 1)
            return redirect(url, code=301)


@app.after_request
def add_header(response):
    response.cache_control.max_age = 300
    return response


# -----------------------LOGIN MANAGER-----------------------
class User(flask_login.UserMixin):
    def __init__(self, email):
        self.id = ""
        self.email = email


connection = Database.open_connection()
users = [User(x) for x in main.get_all_users()]
Database.close_connection()


@login_manager.user_loader
def user_loader(email):
    user = User(email)
    user.id = email
    return user


@login_manager.request_loader
def request_loader(request):
    email = request.form.get('emaillogin')
    user = User(email)
    user.id = email
    return user


# -----------------------FILE EXTENSIONS-----------------------
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# -----------------------TEMPLATE GLOBAL VARIABLES-----------------------

@app.context_processor
@postgres_connection
def get_locale():
    homepage = main.get_setting_by_name('is_homepage_session')[0]
    session[main.get_setting_by_name('is_homepage_session')[0]] = False
    preferred_language = session.get("preferred_language", default='ko_KR')
    web_translations = main.read_table('web_translations')
    session['url'] = request.url
    korean_translation = {}
    english_translation = {}
    for x in web_translations:
        key = x[1]
        korean_translation[key] = x[2]
        english_translation[key] = x[3]
    if preferred_language == 'ko_KR':
        return dict(msgid=korean_translation, nav_menu_admin=nav_menu_admin, menu_item_home=menu_item_home,
                    homepage=homepage, preferred_language=preferred_language)
    else:
        return dict(msgid=english_translation, nav_menu_admin=nav_menu_admin, menu_item_home=menu_item_home,
                    homepage=homepage, preferred_language=preferred_language)


# -----------------------RQ-----------------------

# @rq.job
def send_sms_in_background(message_str):
    naver_setup.send_message_admin(message=message_str)


# @rq.job
def send_email_in_background(message_object):
    mail.send(message=message_object)


# -----------------------PUBLIC-----------------------
@app.route("/lang_<lang>", methods=['GET', 'POST'])
def set_language(lang):
    if lang == 'ko_KR' or lang == 'en':
        session["preferred_language"] = lang
    else:
        session["preferred_language"] = 'ko_KR'
    return redirect(session['url'])


@app.route("/", methods=['GET', 'POST'])
@postgres_connection
def index():
    session[main.get_setting_by_name('is_homepage_session')[0]] = True
    api_kakao_js = main.get_setting_by_name('kakaoAPI')[1]
    best_products = []
    contact_form = ContactForm()
    news_articles = main.read_table('news')
    products = main.read_table('products')
    for row in products:
        if row[8] == True:
            row_list = [x for x in row]
            if not os.path.exists(os.path.abspath("static/img/products") + "/" + row[5]):
                row_list[5] = "no-image-available.jpg"
            best_products.append(row_list)
    if request.method == "POST":
        input_list = (
            contact_form.name.data, contact_form.phone.data, contact_form.email.data, contact_form.message.data,
            contact_form.subject.data)
        form_error = ""
        suspicious_request = False
        for input_item in input_list:
            if input_item == None or input_item == 'None':
                form_error = input_item + ": has None. MESSAGE>>;; " + str(input_list)
                suspicious_request = True
                break
        # msg.recipients = ["rlatnals3020@naver.com"]
        if suspicious_request:
            admin_msg = Message("Coup De Foudre: Suspicious request",
                                sender="from@example.com",
                                recipients=["to@example.com"])
            admin_msg.recipients = ["cdfguri@gmail.com"]
            message = form_error + str(request.data) + '\n' + str(request.args) + '\n' + str(request.form) + '\n' + str(
                request.files) + '\n' + str(request.values) + '\n' + str(request.json) + '\n'
            admin_msg.html = message
            try:
                send_email_in_background(admin_msg)
                app.logger.error('suspicious_request: ' + form_error)
            except Exception as e:
                app.logger.error(str(e) + ': Mail couldn\'t be send')
        else:
            admin_msg = Message("Coup De Foudre: 문의 주세요!",
                                sender="from@example.com",
                                recipients=["to@example.com"])
            admin_msg.recipients = ["cdfguri@gmail.com"]
            message = f"<b>띵동! {contact_form.name.data}한테 메시지가 왔어요!! <br> 성명: {contact_form.name.data}<br>주소: {contact_form.address.data}<br>전화번호: {contact_form.phone.data}<br>이메일주소: {contact_form.email.data}<br>제목: {contact_form.subject.data}<br>주요 메시지: {contact_form.message.data} <br> 더보기: https://cdf.herokuapp.com/contact_inquiry</b>"
            admin_msg.html = message
            try:
                send_email_in_background(admin_msg)
            except Exception as e:
                app.logger.error(str(e) + ': Mail couldn\'t be send')
            try:
                send_sms_in_background(f"문의 주세요! ({contact_form.phone.data}) {contact_form.name.data}")
                send_sms_in_background("더보기: https://cdf.herokuapp.com/contact_inquiry")
            except Exception as e:
                app.logger.error(str(e) + ': Naver SMS couldn\'t be send')
            Database.Contact(name=contact_form.name.data, email=contact_form.email.data,
                             address=contact_form.address.data,
                             phone=contact_form.phone.data, subject=contact_form.subject.data,
                             message=contact_form.message.data).register_contact_query()
    return render_template('index.html', api_kakao_js=api_kakao_js, products=best_products, contact_form=contact_form,
                           news_articles=news_articles)


@app.route("/products", methods=['GET', 'POST'])
@postgres_connection
def products():
    products = []
    data_products = main.read_table('products')
    data_allergenproduct = main.read_table('allergenproduct')
    data_allergens = main.read_table('allergens')
    allergenproduct = {}
    for x in data_allergenproduct:
        if x[1] in allergenproduct:
            allergenproduct[x[1]].append({x[2]: x[3]})
        else:
            allergenproduct[x[1]] = [{x[2]: x[3]}]
    for p in allergenproduct:
        prod_list = {}
        for a in allergenproduct[p]:
            prod_list.update(a)
        allergenproduct[p] = prod_list
    korean_allergens = {}
    english_allergens = {}
    for row in data_allergens:
        korean_allergens[row[0]] = row[2]
        english_allergens[row[0]] = row[1]
    for row in data_products:
        row_list = [x for x in row]
        if not os.path.exists(os.path.abspath("static/img/products") + "/" + row[5]):
            row_list[5] = "no-image-available.jpg"
        products.append(row_list)
    return render_template('products.html', products=products, korean_allergens=korean_allergens,
                           english_allergens=english_allergens,
                           allergenproduct=allergenproduct)


@app.route('/large_order_price', methods=['GET', 'POST'])
@postgres_connection
def large_order_price():
    products = main.read_table('products')
    return render_template('large_orders_price.html', products=products)


@app.route("/allergens", methods=['GET', 'POST'])
@postgres_connection
def allergens():
    products = main.read_table('products')
    allergens = main.read_table('allergens')
    common_allergens = [2, 3, 5, 8, 9]
    return render_template('allergens.html', product_list=main.allergen_dict_all_products(), products=products,
                           allergens=allergens,
                           common_allergens=common_allergens)


@app.route("/privacy_policy", methods=['GET', 'POST'])
def privacy_policy():
    return render_template('privacy_policy.html')


@app.route('/robots.txt')
def robot_file():
    return render_template("Robots.txt")


@app.route("/naver_review", methods=['GET', 'POST'])
def naver_review():
    return redirect("https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=0&ie=utf8&query=coupdefoudre")


#
# @app.route("/register_membership", methods=['GET', 'POST'])
# @flask_login.login_required
# def add_membership():
#     if request.method == "POST":
#         if "get_verification" in request.form:
#             if session.get('verification_code'):
#                 time_now = pytz.utc.localize(datetime.datetime.now() - timedelta(minutes=5))
#                 time_verification = session['verification_code'][1]
#                 if time_now > time_verification:
#                     session.pop('verification_code')
#             if not session.get('verification_code'):
#                 session['verification_code'] = (random.randint(100000, 999999), datetime.datetime.now())
#             phone_number = request.form['phone_number']
#             for char in string.punctuation:
#                 phone_number = phone_number.replace(char, '')
#             phone_number = phone_number.replace(' ', '')
#             if main.phone_number_exists(phone_number):
#                 return make_response(
#                     jsonify({'message': 'Phone number: ' + phone_number + ' exists.', 'code': 'ERROR'}), 201)
#             else:
#                 session['member_registration'] = {'first_name': request.form['first_name'],
#                                                   'last_name': request.form['last_name'], 'phone_number': phone_number}
#                 naver_setup.send_notification_code(to_no=phone_number, code=session['verification_code'][0],
#                                                    language=session["preferred_language"])
#                 return make_response(jsonify(
#                     {'message': 'The verification code has been sent to ' + phone_number + ".", 'code': 'SUCCESS'}),
#                     201)
#         elif "check_verification" in request.form:
#             if session.get('verification_code'):
#                 if request.form['verification_code'] == str(session['verification_code'][0]):
#                     Database.Membership(session['member_registration']['first_name'],
#                                         session['member_registration']['last_name'],
#                                         session['member_registration']['phone_number'], points=2000).register()
#                     session.pop('member_registration')
#                     return make_response(jsonify({'message': 'Verification completed', 'code': 'SUCCESS'}), 201)
#                 else:
#                     return make_response(
#                         jsonify({'message': 'Verification error: The codes did not match', 'code': 'ERROR'}), 201)
#             else:
#                 return make_response(jsonify({'message': 'Verification code can be expired.', 'code': 'ERROR'}), 201)
#
#     return render_template("add_membership.html")
#
#
# @app.route("/membership", methods=['GET', 'POST'])
# @flask_login.login_required
# def check_membership():
#     membership_data = main.read_table('memberships')
#     if request.method == "POST":
#         if "verification_request" in request.form:
#             if request.form['phone_number'] not in [x[1] for x in membership_data]:
#                 flash("Phone number is not registered yet.")
#                 redirect(url_for('add_membership'))
#             elif session.get('verification_code'):
#                 if session['verification_code'][1] + datetime.timedelta(minutes=5) <= datetime.datetime.now():
#                     session['verification_code'] = (random.randint(100000, 999999), datetime.datetime.now())
#                     flash("Verification code expired. A new code has been sent.")
#                     naver_setup.send_notification_code(to_no=request.form['phone_number'],
#                                                        code=session['verification_code'][0],
#                                                        language=session["preferred_language"])
#                 else:
#                     flash("Verification code is not expired yet. The code has been resent.")
#                     naver_setup.send_notification_code(to_no=request.form['phone_number'],
#                                                        code=session['verification_code'][0],
#                                                        language=session["preferred_language"])
#             else:
#                 session['verification_code'] = (random.randint(100000, 999999), datetime.datetime.now())
#
#         elif "verification_validation" in request.form:
#             if session.get('verification_code'):
#                 if session['verification_code'][1] + datetime.timedelta(minutes=5) <= datetime.datetime.now():
#                     flash("Verification code is not correct.")
#                     redirect(url_for('check_membership'))
#
#                     if session['verification_code'][1] == request.form['given_verification_code']:
#                         flash("Verification code has been verified.")
#                         redirect(url_for('check_membership'))
#                 else:
#                     flash("Verification code expired. Send a new code. ")
#             else:
#                 flash("Verification code is not created yet.")
#
#         elif "request_membership_points" in request.form:
#             if request.form["verification_code"] == session['verification_code'][0] and session['verification_code'][
#                 1] + datetime.timedelta(minutes=5) >= datetime.datetime.now():
#                 flash("Verification succeeded")
#             else:
#                 if request.form["verification_code"] != session['verification_code'][0]:
#                     flash("Verification failed: code doesn't match")
#                 elif session['verification_code'][1] + datetime.timedelta(minutes=5) <= datetime.datetime.now():
#                     flash("Verification failed: code has expired. Try again.")
#                 else:
#                     abort(500)
#             redirect(url_for('add_membership'))
#         redirect(url_for("add_membership"))
#     return render_template("check_membership.html")


# -----------------------ADMIN-----------------------
@app.route('/admin_overview', methods=['GET', 'POST'])
@flask_login.login_required
@postgres_connection
def admin_overview():
    if request.method == 'POST':
        if 'btn_delete_comment' in request.form:
            main.delete_row_by_id('comments', request.form['btn_delete_comment'])
            redirect(url_for('admin_overview'))
        elif 'btn_comment' in request.form:
            comment = Database.Comment(request.form['comment'])
            comment.register_comment()
            redirect(url_for('admin_overview'))
        elif 'btn_news' in request.form:
            news_data = {'1': {}, '2': {}, '3': {}, '4': {}, '5': {}, '6': {}, '7': {}}
            for input_field in request.form:
                if '$$$' in input_field:
                    input_field_sep = input_field.split('$$$')
                    news_data[input_field_sep[0]].update({input_field_sep[1]: request.form[input_field]})
            for news_item in news_data:
                if 'is_published' in news_data[news_item]:
                    is_published = True
                else:
                    is_published = False
                if 'active' in news_data[news_item]:
                    active = True
                else:
                    active = False
                Database.News(english_news_title=news_data[news_item]['english_news_title'],
                              korean_news_title=news_data[news_item]['korean_news_title'],
                              english_news_subtitle=news_data[news_item]['english_news_subtitle'],
                              korean_news_subtitle=news_data[news_item]['korean_news_subtitle'],
                              english_news_details=news_data[news_item]['english_news_details'],
                              korean_news_details=news_data[news_item]['korean_news_details'],
                              lightbox_image=news_data[news_item]['lightbox_image'],
                              display_image=news_data[news_item]['display_image'],
                              active=active,
                              bs_interval=news_data[news_item]['bs_interval'],
                              is_published=is_published,
                              ).update(int(news_item))
        else:
            app.logger.error("Error in admin overview: comment/news is not stored")
    data = {}
    data['comments'] = main.read_table('comments')
    data['news'] = main.read_table('news', order_asc='id')
    data['news_col'] = main.show_columns('news')
    return render_template('admin_overview.html', data=data)


@app.route('/business_plan', methods=['GET', 'POST'])
@flask_login.login_required
@postgres_connection
def business_plan():
    return render_template('business_plan.html')


@app.route('/cost_calculation', methods=['GET', 'POST'])
@flask_login.login_required
@postgres_connection
def cost_calculation():
    allergens = main.read_table('allergens')
    if request.method == 'POST':
        if 'ingredients_add_button' in request.form:
            ingredient = Database.Ingredients(request.form['english'], request.form['korean'],
                                              get_ingredientid=True)
            ingredientid = ingredient.register_ingredient()
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
            product_id = Database.Products(request.form['english'], request.form['korean'],
                                           request.form['weight_in_gram_per_product'], request.form['unit'],
                                           request.form['image'], type=request.form['type'],
                                           currently_selling=currently_selling, best=best_product,
                                           korean_description=request.form['Korean_description'],
                                           english_description=request.form['English_description'],
                                           qr=request.form['QR'], selling_price_lv=request.form['selling_price_lv'],
                                           criteria_lv=request.form['criteria_lv'],
                                           selling_price_mv=request.form['selling_price_mv'],
                                           criteria_mv=request.form['criteria_mv'],
                                           selling_price_hv=request.form['selling_price_hv'],
                                           criteria_hv=request.form['criteria_hv'],
                                           work_time_min=request.form['work_time_min'],
                                           estimated_items=request.form['estimated_items']).register()
            allergens_form_list = [x for x in request.form if 'allergen' in x]
            allergen_dict = {}
            for allergen in allergens:
                allergen_dict[allergen[0]] = False
            for allergen in allergens_form_list:
                allergen_id = allergen.split("$$$")[1]
                allergen_dict[allergen_id] = True
            for key in allergen_dict:
                Database.AllergenProduct(productID=product_id, AllergenID=key,
                                         contains_allergen=allergen_dict[key]).register()

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
                           ingredients=ingredients, products=products,
                           missing_prices_packaging=missing_prices_packaging,
                           missing_prices_ingredients=missing_prices_ingredients, allergens=allergens)


@app.route('/edit_cost_calculation', methods=['GET', 'POST'])
@flask_login.login_required
@postgres_connection
def edit_cost_calculation():
    if request.method == "POST":
        if 'products_edit_button' in request.form:
            if 'currently_selling' in request.form:
                currently_selling = request.form['currently_selling'] == 'on'
            else:
                currently_selling = False
            if 'best_product' in request.form:
                best_product = request.form['best_product'] == 'on'
            else:
                best_product = False
            Database.Products(request.form['english'], request.form['korean'],
                              request.form['weight'], request.form['unit'],
                              request.form['image'], type=request.form['type'],
                              currently_selling=currently_selling, best=best_product,
                              korean_description=request.form['Korean_description'],
                              english_description=request.form['English_description'],
                              qr=request.form['QR'], selling_price_lv=request.form['selling_price_lv'],
                              criteria_lv=request.form['criteria_lv'],
                              selling_price_mv=request.form['selling_price_mv'],
                              criteria_mv=request.form['criteria_mv'],
                              selling_price_hv=request.form['selling_price_hv'],
                              criteria_hv=request.form['criteria_hv'], work_time_min=request.form['work_time_min'],
                              estimated_items=request.form['estimated_items']).update(
                request.form['products_edit_button'])
        elif 'ingredients_edit_button' in request.form:
            Database.Ingredients(request.form['english'], request.form['korean']).update_ingredient(
                request.form['ingredients_edit_button'])
        elif 'packaging_edit_button' in request.form:
            Database.Packaging(request.form['english'], request.form['korean']).update(
                request.form['packaging_edit_button'])
        elif 'prices_ingredients_edit_button' in request.form:
            if request.form['date'] == '':
                date = None
            else:
                date = request.form['date']
            Database.PricesIngredients(request.form['ingredientid'], request.form['price'],
                                       request.form['weight_in_gram'], date).update(
                request.form['prices_ingredients_edit_button'])
        elif 'prices_packaging_edit_button' in request.form:
            if request.form['date'] == '':
                date = None
            else:
                date = request.form['date']
            Database.PricesPackaging(request.form['packagingid'], request.form['price'], date).update(
                request.form['prices_packaging_edit_button'])
        elif 'packaging_product_edit_button' in request.form:
            Database.PackagingProduct(request.form['productid'], request.form['packagingid']).update(
                request.form['packaging_product_edit_button'])
        elif 'ingredient_product_edit_button' in request.form:
            Database.IngredientProduct(request.form['productid'], request.form['ingredientid'],
                                       request.form['weight_in_gram']).update(
                request.form['ingredient_product_edit_button'])
        elif 'products_delete_button' in request.form:
            main.delete_row_by_id('products', request.form['products_delete_button'])
        elif 'ingredients_delete_button' in request.form:
            main.delete_row_by_id('ingredients', request.form['ingredients_delete_button'])
        elif 'packaging_delete_button' in request.form:
            main.delete_row_by_id('packaging', request.form['packaging_delete_button'])
        elif 'prices_ingredients_delete_button' in request.form:
            main.delete_row_by_id('prices_ingredients', request.form['prices_ingredients_delete_button'])
        elif 'prices_packaging_delete_button' in request.form:
            main.delete_row_by_id('prices_packaging', request.form['prices_packaging_delete_button'])
        elif 'packaging_product_delete_button' in request.form:
            main.delete_row_by_id('packagingproduct', request.form['packaging_product_delete_button'])
        elif 'ingredient_product_delete_button' in request.form:
            main.delete_row_by_id('ingredientproduct', request.form['ingredient_product_delete_button'])
        else:
            app.logger.error('Minor bug alert. Edit/delete in cost calculation is not performed. ')
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
@flask_login.login_required
@postgres_connection
def financial_plan():
    data = {}
    data['products'] = main.read_table('products')
    if request.method == "POST":
        if 'fixed_cost_edit_button' in request.form or 'fixed_cost_add_button' in request.form:
            fixed_cost = Database.FixedCost(request.form['english'], request.form['korean'],
                                            request.form['cost_per_month'], request.form['one_time_cost'],
                                            request.form['period'])
            if 'fixed_cost_add_button' in request.form:
                fixed_cost.register_cost()
            elif 'fixed_cost_edit_button' in request.form:
                fixed_cost.update_cost(request.form['fixed_cost_edit_button'])

        elif 'fixed_cost_report_button' in request.form:
            if request.form['date'] == '':
                date = datetimelib.now().strftime("%Y-%m-%d")
            else:
                date = request.form['date']
            for key in request.form:
                if 'cost_per_month' in key:
                    values = key.split('$$$')
                    Database.FixedCostReport(values[1], request.form[key], date).register()

        elif 'investment_edit_button' in request.form or 'investment_add_button' in request.form:

            investment = Database.Investment(request.form['english'], request.form['korean'],
                                             request.form['min_price'], request.form['max_price'])
            if 'investment_add_button' in request.form:
                investment.register_investment()
            elif 'investment_edit_button' in request.form:
                investment.update_investment(request.form['investment_edit_button'])
        elif 'btn_delete_fixed_cost' in request.form:
            main.delete_row_by_id('fixed_costs', request.form['btn_delete_fixed_cost'])
        elif 'btn_delete_investment' in request.form:
            main.delete_row_by_id('investments', int(request.form['btn_delete_investment']))

        elif 'btn_delete_sale' in request.form:
            main.delete_row_by_id('sales', request.form['btn_delete_sale'])
        elif 'btn_delete_sale_summary' in request.form:
            main.delete_row_by_date('sales', request.form['btn_delete_sale_summary'])

        elif 'change_products_report' in request.form:
            for x in data['products']:
                if str(x[0]) in request.form:
                    Database.Products(x[1], x[2], x[3], x[4], x[5], x[6], x[7], x[8], x[9], x[10], x[11],
                                      request.form['price_low_amount_' + str(x[0])], x[13],
                                      request.form['price_medium_amount_' + str(x[0])], x[15],
                                      request.form['price_high_amount_' + str(x[0])], x[17],
                                      request.form['amount_low_' + str(x[0])], x[19]).update(x[0])
        elif 'add_financial_report' in request.form:
            data['vat'] = {}
            data['turnover-after-vat'] = {}
            data['variable-costs'] = main.calculate_variable_cost()['total_average']
            data['breakeven-per-product'] = {}
            for product in data['products']:
                data['vat'][product[0]] = int(product[12] - (product[12] / 1.1))
                data['turnover-after-vat'][product[0]] = int(product[12] / 1.1)
                data['breakeven-per-product'][product[0]] = int(
                    (product[12] / 1.1) - data['variable-costs'][product[0]])
            if request.form['date'] == '':
                input_date = None
            else:
                input_date = request.form['date']
            for product in data['products']:
                if str(product[0]) in request.form:
                    sold_products = int(request.form['amount_low_' + str(product[0])]) + int(
                        request.form['amount_medium_' + str(product[0])]) + int(
                        request.form['amount_high_' + str(product[0])])
                    total_variable_cost = sold_products * int(data['variable-costs'][product[0]])
                    low = int(request.form['price_low_amount_' + str(product[0])]) * int(
                        request.form['amount_low_' + str(product[0])])
                    medium = int(request.form['price_medium_amount_' + str(product[0])]) * int(
                        request.form['amount_medium_' + str(product[0])])
                    high = int(request.form['price_high_amount_' + str(product[0])]) * int(
                        request.form['amount_high_' + str(product[0])])
                    total_income = low + medium + high
                    vat = int(total_income - (total_income / 1.1))
                    Database.Sale(input_date, request.form['amount_low_' + str(product[0])],
                                  request.form['price_low_amount_' + str(product[0])],
                                  request.form['amount_medium_' + str(product[0])],
                                  request.form['price_medium_amount_' + str(product[0])],
                                  request.form['amount_high_' + str(product[0])],
                                  request.form['price_high_amount_' + str(product[0])],
                                  str(product[0]),
                                  str(total_variable_cost),
                                  str(total_income),
                                  str(vat)).register()
        elif 'add_financial_report_simplified' in request.form:
            data['vat'] = {}
            data['turnover-after-vat'] = {}
            data['variable-costs'] = main.calculate_variable_cost()['total_average']
            data['breakeven-per-product'] = {}
            for product in data['products']:
                data['vat'][product[0]] = int(product[12] - (product[12] / 1.1))
                data['turnover-after-vat'][product[0]] = int(product[12] / 1.1)
                data['breakeven-per-product'][product[0]] = int(
                    (product[12] / 1.1) - data['variable-costs'][product[0]])
            if request.form['date'] == '':
                input_date = None
            else:
                input_date = request.form['date']
            for product in data['products']:
                if str(product[0]) in request.form:
                    sold_products = int(request.form['amount_low_' + str(product[0])])
                    total_variable_cost = sold_products * int(data['variable-costs'][product[0]])
                    total_income = int(request.form['price_low_amount_' + str(product[0])]) * int(
                        request.form['amount_low_' + str(product[0])])
                    vat = int(total_income - (total_income / 1.1))
                    Database.Sale(input_date, request.form['amount_low_' + str(product[0])],
                                  request.form['price_low_amount_' + str(product[0])],
                                  0, 0, 0, 0, str(product[0]), str(total_variable_cost), str(total_income),
                                  str(vat)).register()
        else:
            abort(500)
    data['products'] = main.read_table('products')
    data['products-col'] = main.show_columns('products')
    data['total'] = {'minimum': 0, 'maximum': 0, 'total_cost': 0}
    data['investments'] = []
    for row in main.read_table('investments'):
        row = [col for col in row]
        data['total']['minimum'] += int(row[3])
        data['total']['maximum'] += int(row[4])
        data['investments'].append(row)
    data['fixed_costs'] = []
    for row in main.read_table('fixed_costs'):
        row = [row[0], row[1], row[2], row[4], row[5], row[6]]
        data['total']['total_cost'] += row[3]
        data['fixed_costs'].append(row)
    data['vat'] = {}
    data['turnover-after-vat'] = {}
    data['variable-costs'] = main.calculate_variable_cost()['total_average']
    data['breakeven-per-product'] = {}
    for product in data['products']:
        data['vat'][product[0]] = int(product[12] - (product[12] / 1.1))
        data['turnover-after-vat'][product[0]] = int(product[12] / 1.1)
        data['breakeven-per-product'][product[0]] = int((product[12] / 1.1) - data['variable-costs'][product[0]])
    data['sales'] = {}
    data['sales_summary'] = {}
    data['sales_month_summary'] = {}
    data['sales_columns'] = main.show_columns('sales')
    data['all_sales'] = main.read_table('sales')
    for x in data['all_sales']:
        if x[1].date() in data['sales']:
            data['sales'][x[1].date()] += [x]
        else:
            data['sales'][x[1].date()] = [x]
        if x[1].date() not in data['sales_summary']:
            breakeven = x[10] - (x[9] + x[11])
            data['sales_summary'][x[1].date()] = {"Total Turnover": x[10], "VAT": x[11], "Variable Costs": x[9],
                                                  'Break Even': breakeven}
        else:
            data['sales_summary'][x[1].date()]["Total Turnover"] += x[10]
            data['sales_summary'][x[1].date()]['VAT'] += x[11]
            data['sales_summary'][x[1].date()]['Variable Costs'] += x[9]
            breakeven = x[10] - (x[9] + x[11])
            data['sales_summary'][x[1].date()]['Break Even'] += breakeven
        year_month = str(x[1].year) + "-" + str(x[1].month)
        if year_month not in data['sales_month_summary']:
            breakeven = x[10] - (x[9] + x[11])
            data['sales_month_summary'][year_month] = {"Total Turnover": x[10], "VAT": x[11], "Variable Costs": x[9],
                                                       'Break Even': breakeven}
        else:
            data['sales_month_summary'][year_month]["Total Turnover"] += x[10]
            data['sales_month_summary'][year_month]['VAT'] += x[11]
            data['sales_month_summary'][year_month]['Variable Costs'] += x[9]
            breakeven = x[10] - (x[9] + x[11])
            data['sales_month_summary'][year_month]['Break Even'] += breakeven
    for month in data['sales_month_summary']:
        data['sales_month_summary'][month]['Break Even']=data['sales_month_summary'][month]['Break Even']-data['total']['total_cost']
    data['sales_summary'] = collections.OrderedDict(sorted(data['sales_summary'].items(), reverse=True))
    data['sales_month_summary'] = collections.OrderedDict(sorted(data['sales_month_summary'].items(), reverse=True))

    return render_template('financial_plan.html', data=data)


@app.route('/loss_calculator', methods=['GET', 'POST'])
@flask_login.login_required
@postgres_connection
def loss_calculator():
    data = {}
    data['products'] = main.read_table('products')
    data['vat'] = {}
    data['turnover-after-vat'] = {}
    data['variable-costs'] = main.calculate_variable_cost()['total_average']
    data['breakeven-per-product'] = {}
    for product in data['products']:
        data['vat'][product[0]] = int(product[12] - (product[12] / 1.1))
        data['turnover-after-vat'][product[0]] = int(product[12] / 1.1)
        data['breakeven-per-product'][product[0]] = int((product[12] / 1.1) - data['variable-costs'][product[0]])
    return render_template('loss_calculator.html', data=data)


@app.route('/invoices', methods=['GET', 'POST'])
@flask_login.login_required
@postgres_connection
def invoices():
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
                    date = datetimelib.now().strftime("%Y-%m-%d")
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
                    date = datetimelib.now().strftime("%Y%m%d_%H%M%S")
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
@flask_login.login_required
def images():
    return render_template('images.html', cloud_images=[])


@app.route('/contact_inquiry', methods=['GET', 'POST'])
@flask_login.login_required
@postgres_connection
def contact_inquiry():
    if request.method == 'POST':
        naver_setup.send_sms_to_receiver(message=request.form['message'],
                                         phone_receiver=request.form['phone_number'])
        flash('메시지를 보냈어요!!')
    contact_info = main.read_table('customer_contact_submission', order_desc="time")
    return render_template('contact_inquiry.html', contact_info=contact_info)


@app.route('/recipes', methods=['GET', 'POST'])
@flask_login.login_required
@postgres_connection
def recipes():
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
@flask_login.login_required
@postgres_connection
def cost_per_product():
    return render_template('cost_per_product.html', data=main.calculate_variable_cost())


@app.route('/translations', methods=['GET', 'POST'])
@flask_login.login_required
@postgres_connection
def translations():
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
@flask_login.login_required
@postgres_connection
def qr_info():
    if request.method == 'POST':
        for key in request.form:
            if 'product_' in key:
                img = qrcode.make(request.form[key])
                img.save("/static/img/QR/" + request.form[key] + ".png")
        return render_template('qr_info.html')
    return render_template('qr_info.html')


@app.route('/print_ingredient_list', methods=['GET', 'POST'])
@flask_login.login_required
@postgres_connection
def print_ingredient_list():
    data_dictionary = {}
    data_dictionary['ingredients'] = main.read_table('ingredients')
    data_dictionary['ingredients_col'] = main.show_columns('ingredients')
    data_dictionary['packaging'] = main.read_table('packaging')
    data_dictionary['packaging_col'] = main.show_columns('packaging')
    data_dictionary['length_ingredients'] = int(len(data_dictionary['ingredients']) / 2)
    data_dictionary['length_packaging'] = int(len(data_dictionary['packaging']) / 2)
    html = render_template('print_ingredient_list.html', data_dictionary=data_dictionary)
    return html


@app.route("/edit_allergens", methods=['GET', 'POST'])
@flask_login.login_required
@postgres_connection
def edit_allergens():
    if request.method == "POST":
        if 'submit_allergen_modifications' in request.form:
            allergenproducts = main.read_table('allergenproduct')
            allergens_check = {}
            for allergenproduct in allergenproducts:
                allergens_check[str(allergenproduct[1]) + '$$$' + str(allergenproduct[2])] = False
            for field in request.form:
                if '$$$' in field:
                    allergens_check[field] = True
            for key in allergens_check:
                op = key.split('$$$')
                Database.AllergenProduct(productID=op[0], AllergenID=op[1],
                                         contains_allergen=allergens_check[key]).update()
    products = main.read_table('products')
    allergens = main.read_table('allergens')
    return render_template('allergens_edit.html', product_list=main.allergen_dict_all_products(), products=products,
                           allergens=allergens)


# ----------------------LOG IN/OUT-----------------------------
@app.route('/login', methods=['GET', 'POST'])
@postgres_connection
def login():
    cform = LoginForm()
    if cform.validate_on_submit():
        if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
            request_ip = request.environ['REMOTE_ADDR']
        else:
            request_ip = request.environ['HTTP_X_FORWARDED_FOR']
        if request_ip not in trusted_ip:
            admin_msg = Message("Coup De Foudre: 문의 주세요!",
                                sender="from@example.com",
                                recipients=["cdfguri@gmail.com"],
                                html='suspicious login attempt: ' + request_ip)
            try:
                send_email_in_background(admin_msg)
            except Exception as e:
                app.logger.error(str(e) + ': Login attempt mail couldn\'t be send')
        email = cform.email.data
        user = User(email)
        app.logger.warning('Validated attempt to login.')
        if user in users and main.verify_password(email, cform.password.data):
            app.logger.info(email + ' is logged in as admin.')
            flask_login.login_user(user=user, remember=True)
            return redirect(url_for('contact_inquiry'))
        else:
            return redirect(url_for('login'))
    return render_template('login.html', form=cform)


@app.route("/logout")
def logout():
    flask_login.logout_user()
    return redirect(url_for('login'))


@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect(url_for('login'))


# ----------------------ERROR HANDLING-----------------------------

@app.errorhandler(400)
def bad_request(e):
    e_friendly = "The server and client don't seem to have any manners"
    return render_template('error.html', e=e, e_friendly=e_friendly), 400


@app.errorhandler(401)
def bad_request(e):
    e_friendly = "The bad guys don't come in. I have my laser taser"
    return render_template('error.html', e=e, e_friendly=e_friendly), 401


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
