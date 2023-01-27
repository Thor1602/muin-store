import os
from os.path import exists

from werkzeug.security import generate_password_hash, check_password_hash
from psycopg2 import Error
import psycopg2
import random
import string

import googledrive_connector

connection = None
cur = None


def open_connection():
    try:
        global connection
        global cur
        if exists(
                'D:\\Users\\Thorben\\OneDrive - University of the People\\PycharmProjects\\bakery\\gitignore\\database_credentials.txt'):
            credentials = str(open(
                "D:\\Users\\Thorben\\OneDrive - University of the People\\PycharmProjects\\bakery\\gitignore\\database_credentials.txt",
                'r').read())
            connection = psycopg2.connect(credentials, sslmode='require')
        else:
            DATABASE_URL = os.environ['DATABASE_URL']
            connection = psycopg2.connect(DATABASE_URL, sslmode='require')
        cur = connection.cursor()
    except Error as e:
        print(e)


def execute_query(query, parameters=(), commit=False, fetchAll=False, fetchOne=False):
    try:
        global connection
        global cur
        result = None
        cur.execute(query, parameters)
        if commit:
            connection.commit()
        if fetchAll:
            result = [row for row in cur.fetchall()]
        elif fetchOne:
            result = cur.fetchone()[0]

        return result
    except Error as e:
        print(e)


def close_connection():
    try:
        connection.close()
        cur.close()
    except Error as e:
        print(e)


class Main:
    """
        This main class of the database helper is:
            - to execute all types of queries
            - read a table in the database
            - delete an entry in a table in the database
    """

    def show_tables(self):
        SQL = """SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"""
        return execute_query(query=SQL, fetchAll=True)

    def show_columns(self, table_name):
        SQL = "SELECT column_name FROM information_schema.columns WHERE table_name = %s;"
        parameters = (table_name,)
        return [x[0] for x in execute_query(query=SQL, parameters=parameters, fetchAll=True)]

    def read_table(self, table_name, order_asc="", order_desc="", return_field=""):
        argument = ""
        if order_asc != "":
            argument = f"order by {order_asc} asc"
        if order_desc != "":
            argument = f"order by {order_desc} desc"
        if return_field != "":
            argument = f"returning {return_field}"
        SQL = f"SELECT * from {table_name} {argument};"
        return execute_query(query=SQL, fetchAll=True)

    def create_table(self, table_name, columns):
        columns = ", ".join(columns)
        columns = "id SERIAL PRIMARY KEY, " + columns
        SQL = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns});"
        return execute_query(query=SQL, commit=True)

    def get_row_by_id(self, cursor, id, table_name):
        SQL = "SELECT * from %(table_name)s where id = %(id)s;"
        parameters = {'table_name': table_name, 'id': id}
        query = cursor.execute(query=SQL, parameters=parameters)
        return query.fetchOne()

    def delete_row_by_id(self, table_name, id):
        SQL = f"DELETE from {table_name} where id = {id};"
        # parameters = (table_name, id)
        execute_query(query=SQL, commit=True)

    def verify_password(self, email, pwd):
        retrieved_password = execute_query(query="SELECT value FROM settings where key = %s;", parameters=(email,),
                                           fetchOne=True)
        return check_password_hash(retrieved_password, pwd)

    def get_all_users(self):
        users = execute_query(query="SELECT key FROM settings where name = 'login';", fetchAll=True)
        return [x[0] for x in users]

    def random_string_generator(self, N):
        chars = string.digits + string.punctuation + string.ascii_letters
        return ''.join(random.SystemRandom().choice(chars.replace("'\"", "")) for _ in range(N))

    def fetch_variable_costs(self):
        col = ('cost_id', 'english', 'korean', 'variable_cost', 'selling_price_lv', 'criteria_lv', 'selling_price_mv',
               'criteria_mv', 'selling_price_hv', 'criteria_hv', 'unit', 'work_time_min', 'estimated_items',
               'product_ID')
        SQL = "SELECT variable_costs.id, english, korean, variable_cost, selling_price_lv, criteria_lv, selling_price_mv, criteria_mv, selling_price_hv, criteria_hv, unit, work_time_min, estimated_items, productid FROM products JOIN variable_costs ON variable_costs.productID = products.id;"
        return (execute_query(SQL, fetchAll=True), col)

    def add_setting(self, name, key, value):
        execute_query("INSERT INTO settings (name, key, value) VALUES (%s,%s,%s)",
                      (name, key, value,), commit=True)

    def add_column(self, tablename, columname, type, default_value=None):
        execute_query(f"ALTER TABLE {tablename} ADD COLUMN {columname} {type} DEFAULT '{default_value}';",
                      commit=True)
        # main.add_column(tablename='products', columname='type', type='VARCHAR', default_value='pastry')

    def get_setting_by_name(self, name):
        return \
            execute_query(query="SELECT key, value FROM settings where name = '{}';".format(name), fetchAll=True)[
                0]

    def get_cloud_images(self):
        return googledrive_connector.list_all_files(parent='images')

    def get_membership_points(self, phone_number):
        SQL = "SELECT points from memberships where phone_number = %(phone_number)s;"
        parameters = {'phone_number': phone_number}
        query = execute_query(query=SQL, parameters=parameters, fetchOne=True)
        return query

    def phone_number_exists(self, phone_number):
        SQL = "SELECT phone_number from memberships;"
        query = execute_query(query=SQL, fetchAll=True)
        if phone_number in [x[0] for x in query]:
            return True
        else:
            return False

    def missing_prices_ingredients(self):
        missing_prices = []
        price_ingrs = [x[1] for x in self.read_table('prices_ingredients')]
        ingredients = [x[0] for x in self.read_table('ingredients')]
        for ingrid in set(ingredients):
            if ingrid not in set(price_ingrs):
                missing_prices.append(ingrid)
        return missing_prices

    def missing_prices_packaging(self):
        missing_prices = []
        price_packaging = [x[1] for x in self.read_table('prices_packaging')]
        packaging = [x[0] for x in self.read_table('packaging')]
        for ingrid in set(packaging):
            if ingrid not in set(price_packaging):
                missing_prices.append(ingrid)
        return missing_prices

    def get_price(self, category, get_average=False, get_latest=False, get_all=False):
        all_prices = {}
        if category == 'ingredients':
            price_list = self.read_table('prices_ingredients', order_desc="date")
            for row in price_list:
                if row[1] in all_prices:
                    all_prices[row[1]].append(round(row[2] / row[3], 2))
                else:
                    all_prices[row[1]] = [round(row[2] / row[3], 2)]
            if get_all:
                return all_prices
            elif get_average:
                avg_prices = {}
                for key in all_prices:
                    avg_prices[key] = round(sum(all_prices[key]) / len(all_prices[key]), 2)
                return avg_prices
            elif get_latest:
                latest_prices = {}
                for row in price_list:
                    if row[1] not in latest_prices:
                        latest_prices[row[1]] = round(row[2] / row[3], 2)
                return latest_prices
            else:
                return {}
        elif category == 'packaging':
            price_list = self.read_table('prices_packaging', order_desc="date")
            for row in price_list:
                if row[1] in all_prices:
                    all_prices[row[1]].append(row[2])
                else:
                    all_prices[row[1]] = [row[2]]
            if get_all:
                return all_prices
            elif get_average:
                avg_prices = {}
                for key in all_prices:
                    avg_prices[key] = round(sum(all_prices[key]) / len(all_prices[key]), 2)
                return avg_prices
            elif get_latest:
                latest_prices = {}
                for row in price_list:
                    if row[1] not in latest_prices:
                        latest_prices[row[1]] = row[2]
                return latest_prices
            else:
                return None

    def calculate_variable_cost(self):
        data = {}
        data['ingredients'] = self.read_table('ingredients')
        data['packaging'] = self.read_table('packaging')
        data['packagingproduct'] = self.read_table('packagingproduct')
        data['products'] = self.read_table('products')
        data['ingredientproduct'] = self.read_table('ingredientproduct')

        data['ingredients_get_average'] = self.get_price('ingredients', get_average=True)
        data['ingredients_get_latest'] = self.get_price('ingredients', get_latest=True)
        data['packaging_get_average'] = self.get_price('packaging', get_average=True)
        data['packaging_get_latest'] = self.get_price('packaging', get_latest=True)

        data['total_average_packaging'] = {}
        data['total_latest_packaging'] = {}

        data['total_weight'] = {}
        data['total_average_ingredients'] = {}
        data['total_latest_ingredients'] = {}

        data['total_average_ingredients_per_unit'] = {}
        data['total_average'] = {}
        data['total_latest_ingredients_per_unit'] = {}
        data['total_latest'] = {}

        for packagingproduct in data['packagingproduct']:
            if packagingproduct[2] in data['packaging_get_average']:
                product_id = packagingproduct[1]
                if product_id in data['total_average_packaging']:
                    data['total_average_packaging'][product_id] += round(
                        data['packaging_get_latest'][packagingproduct[2]], 2)
                else:
                    data['total_average_packaging'][product_id] = round(
                        data['packaging_get_latest'][packagingproduct[2]], 2)
            if packagingproduct[2] in data['packaging_get_latest']:
                product_id = packagingproduct[1]
                if product_id in data['total_latest_packaging']:
                    data['total_latest_packaging'][product_id] += data['packaging_get_latest'][packagingproduct[2]]
                else:
                    data['total_latest_packaging'][product_id] = data['packaging_get_latest'][packagingproduct[2]]

        for ingredientproduct in data['ingredientproduct']:
            if ingredientproduct[1] in data['total_weight']:
                data['total_weight'][ingredientproduct[1]] += ingredientproduct[3]
            else:
                data['total_weight'][ingredientproduct[1]] = ingredientproduct[3]

            if ingredientproduct[2] in data['ingredients_get_average']:
                product_id = ingredientproduct[1]
                if product_id in data['total_average_ingredients']:
                    data['total_average_ingredients'][product_id] += round(
                        ingredientproduct[3] * data['ingredients_get_average'][
                            ingredientproduct[2]], 2)
                else:
                    data['total_average_ingredients'][product_id] = round(
                        ingredientproduct[3] * data['ingredients_get_average'][
                            ingredientproduct[2]], 2)

            if ingredientproduct[2] in data['ingredients_get_latest']:
                product_id = ingredientproduct[1]
                if product_id in data['total_latest_ingredients']:
                    data['total_latest_ingredients'][product_id] += round(
                        ingredientproduct[3] * data['ingredients_get_latest'][
                            ingredientproduct[2]], 2)
                else:
                    data['total_latest_ingredients'][product_id] = round(
                        ingredientproduct[3] * data['ingredients_get_latest'][
                            ingredientproduct[2]], 2)

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

            if data['total_average_ingredients'][product[0]] == 0:
                data['total_average_ingredients_per_unit'][product[0]] = 0
            else:
                data['total_average_ingredients_per_unit'][product[0]] = round(
                    data['total_average_ingredients'][product[0]] / (data['total_weight'][product[0]] / product[3]), 2)
            data['total_average'][product[0]] = round(
                data['total_average_ingredients_per_unit'][product[0]] + data['total_average_packaging'][product[0]], 0)

            if data['total_latest_ingredients'][product[0]] == 0:
                data['total_latest_ingredients_per_unit'][product[0]] = 0
            else:
                data['total_latest_ingredients_per_unit'][product[0]] = round(
                    data['total_latest_ingredients'][product[0]] / (data['total_weight'][product[0]] / product[3]), 2)
            data['total_latest'][product[0]] = round(
                data['total_latest_ingredients_per_unit'][product[0]] + data['total_latest_packaging'][product[0]], 0)
        return data

    def allergen_dict_all_products(self):
        product_list = {}
        allergenproduct = self.read_table('allergenproduct')
        for x in allergenproduct:
            if x[1] in product_list:
                product_list[x[1]].append({x[2]: x[3]})
            else:
                product_list[x[1]] = [{x[2]: x[3]}]

        for p in product_list:
            prod_list = {}
            for a in product_list[p]:
                prod_list.update(a)
            product_list[p] = prod_list
        return product_list


class User(Main):
    def __init__(self, nickname, password, role, first_name, last_name, email, last_login):
        self.first_name = first_name
        self.last_name = last_name
        self.nickname = nickname
        self.password = generate_password_hash(password)
        self.role_name = role
        self.email = email
        self.last_login = last_login

    def register_user(self):
        SQL = "INSERT INTO user (first_name, last_name, nickname, password, role_name, email, last_login) VALUES (%s,%s,%s,%s,%s,%s,%s);"
        parameters = (
            self.first_name, self.last_name, self.nickname, self.password, self.role_name, self.email, self.last_login)
        execute_query(query=SQL, parameters=parameters, commit=True)


class Membership(Main):
    def __init__(self, first_name, last_name, phone_number, points):
        self.first_name = first_name
        self.last_name = last_name
        self.phone_number = phone_number
        self.points = points

    def register(self):
        SQL = "INSERT INTO memberships (first_name, last_name, phone_number, points) VALUES (%s,%s,%s,%s);"
        parameters = (self.first_name, self.last_name, self.phone_number, self.points,)
        execute_query(query=SQL, parameters=parameters, commit=True)

    def update_points(self, inserted_phone_number, points_of_current_sale):
        query = "SELECT points from memberships where phone_number = %(phone_number)s;"
        parameters = {'phone_number': inserted_phone_number}
        collected_points = execute_query(query=query, parameters=parameters, fetchOne=True)
        collected_points += points_of_current_sale
        SQL = "UPDATE memberships SET points = %s WHERE phone_number = %s;"
        parameters = (
            collected_points, self.phone_number, inserted_phone_number,)
        execute_query(query=SQL, parameters=parameters, commit=True)


class Contact(Main):
    def __init__(self, name, email, address, phone, subject, message):
        self.name = name
        self.email = email
        self.address = address
        self.phone = phone
        self.subject = subject
        self.message = message

    def register_contact_query(self):
        SQL = "INSERT INTO customer_contact_submission (name, email, address, phone, subject, message, time, isrepliedto) VALUES (%s,%s,%s,%s,%s,%s,now()::timestamp, FALSE);"
        parameters = (self.name, self.email, self.address, self.phone, self.subject, self.message)
        execute_query(query=SQL, parameters=parameters, commit=True)

    def isRead(self, id):
        SQL = "UPDATE customer_contact_submission SET isrepliedto = TRUE WHERE id = %s;"
        parameters = (id,)
        execute_query(query=SQL, parameters=parameters, commit=True)


class OnlineOrder(Main):
    def __init__(self, name, email, phone, order, note):
        self.name = name
        self.email = email
        self.phone = phone
        self.order = order
        self.note = note

    def register_contact_query(self):
        SQL = "INSERT INTO online_order (name, email, phone, subject, message, time, isCompleted) VALUES (%s,%s,%s,%s,%s,now()::timestamp, FALSE);"
        parameters = (self.name, self.email, self.phone, self.order, self.note,)
        execute_query(query=SQL, parameters=parameters, commit=True)

    def isCompleted(self, id):
        SQL = "UPDATE online_order SET isCompleted = TRUE WHERE id = %s;"
        parameters = (id,)
        execute_query(query=SQL, parameters=parameters, commit=True)


class Investment(Main):
    def __init__(self, english, korean, min_price, max_price):
        self.english = english
        self.korean = korean
        self.min_price = min_price
        self.max_price = max_price

    def register_investment(self):
        SQL = "INSERT INTO investments (english, korean, min_price, max_price) VALUES (%s,%s,%s,%s);"
        parameters = (self.english, self.korean, self.min_price, self.max_price,)
        execute_query(query=SQL, parameters=parameters, commit=True)

    def update_investment(self, id):
        SQL = "UPDATE investments SET english = %s, korean = %s, min_price = %s, max_price = %s WHERE id = %s;"
        parameters = (self.english, self.korean, self.min_price, self.max_price, id)
        execute_query(query=SQL, parameters=parameters, commit=True)


class FixedCost(Main):
    def __init__(self, english_name, korean_name, cost_per_month, one_time_cost, period_months):
        self.english_name = english_name
        self.korean_name = korean_name
        self.cost_per_month = cost_per_month
        self.one_time_cost = one_time_cost
        self.period_months = period_months

    def register_cost(self):
        SQL = "INSERT INTO fixed_costs (english_name, korean_name, cost_per_month, one_time_cost, period_months) VALUES (%s,%s,%s,%s,%s);"
        parameters = (self.english_name, self.korean_name, self.cost_per_month, self.one_time_cost, self.period_months,)
        execute_query(query=SQL, parameters=parameters, commit=True)

    def update_cost(self, id):
        SQL = "UPDATE fixed_costs SET english_name = %s, korean_name = %s, cost_per_month = %s, one_time_cost = %s, period_months = %s WHERE id = %s;"
        parameters = (
            self.english_name, self.korean_name, self.cost_per_month, self.one_time_cost, self.period_months, id,)
        execute_query(query=SQL, parameters=parameters, commit=True)


class VariableCost(Main):
    def __init__(self, productid, variable_cost, selling_price_lv, criteria_lv, selling_price_mv, criteria_mv,
                 selling_price_hv, criteria_hv, work_time_min, estimated_items):
        self.productid = productid
        self.variable_cost = variable_cost
        self.selling_price_lv = selling_price_lv
        self.criteria_lv = criteria_lv
        self.selling_price_mv = selling_price_mv
        self.criteria_mv = criteria_mv
        self.selling_price_hv = selling_price_hv
        self.criteria_hv = criteria_hv
        self.work_time_min = work_time_min
        self.estimated_items = estimated_items

    def register_cost(self):
        SQL = "INSERT INTO variable_costs (productid, variable_cost, selling_price_lv, criteria_lv,selling_price_mv, criteria_mv,selling_price_hv, criteria_hv, work_time_min, estimated_items) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
        parameters = (
            self.productid, self.variable_cost, self.selling_price_lv, self.criteria_lv, self.selling_price_mv,
            self.criteria_mv, self.selling_price_hv, self.criteria_hv, self.work_time_min,
            self.estimated_items,)
        execute_query(query=SQL, parameters=parameters, commit=True)

    def update_cost(self, id):
        SQL = "UPDATE variable_costs SET productid = %s, variable_cost = %s, selling_price_lv = %s, criteria_lv = %s, selling_price_mv = %s, criteria_mv = %s, selling_price_hv = %s, criteria_hv = %s, work_time_min = %s, estimated_items = %s WHERE id = %s;"
        parameters = (
            self.productid, self.variable_cost, self.selling_price_lv, self.criteria_lv,
            self.selling_price_mv,
            self.criteria_mv, self.selling_price_hv, self.criteria_hv, self.work_time_min,
            self.estimated_items, id,)
        execute_query(query=SQL, parameters=parameters, commit=True)


class Comment(Main):
    def __init__(self, name):
        self.name = name

    def register_comment(self):
        SQL = "INSERT INTO comments (comment) VALUES (%s);"
        parameters = (self.name,)
        execute_query(query=SQL, parameters=parameters, commit=True)


class Ingredients(Main):
    def __init__(self, english, korean, get_ingredientid=False):
        self.english = english
        self.korean = korean
        self.get_ingredientid = get_ingredientid

    def register_ingredient(self):
        if self.get_ingredientid:
            SQL = "INSERT INTO ingredients (english, korean) VALUES (%s,%s) RETURNING id;"
        else:
            SQL = "INSERT INTO ingredients (english, korean) VALUES (%s,%s);"
        parameters = (self.english, self.korean,)
        return execute_query(query=SQL, parameters=parameters, commit=True, fetchOne=True)

    def update_ingredient(self, id):
        SQL = "UPDATE ingredients SET english = %s, korean = %s WHERE id = %s;"
        parameters = (
            self.english, self.korean, id,)
        execute_query(query=SQL, parameters=parameters, commit=True)


class PricesIngredients(Main):
    def __init__(self, ingredientID, price, weight_in_gram, date=None):
        self.ingredientID = ingredientID
        self.price = price
        self.weight_in_gram = weight_in_gram
        self.date = date

    def register(self):
        if self.date == None:
            SQL = "INSERT INTO prices_ingredients (ingredientid, price, weight_in_gram, date) VALUES (%s,%s,%s,NOW());"
            parameters = (self.ingredientID, self.price, self.weight_in_gram,)
        else:
            SQL = "INSERT INTO prices_ingredients (ingredientid, price, weight_in_gram, date) VALUES (%s,%s,%s,%s);"
            parameters = (self.ingredientID, self.price, self.weight_in_gram, self.date,)
        execute_query(query=SQL, parameters=parameters, commit=True)

    def update(self, id):
        if self.date == None:
            SQL = "UPDATE prices_ingredients SET ingredientID = %s, price = %s, weight_in_gram = %s, date = NOW() WHERE id = %s;"
            parameters = (self.ingredientID, self.price, self.weight_in_gram,)
        else:
            SQL = "UPDATE prices_ingredients SET ingredientID = %s, price = %s, weight_in_gram = %s, date = %s WHERE id = %s;"
            parameters = (self.ingredientID, self.price, self.weight_in_gram, self.date, id,)
        execute_query(query=SQL, parameters=parameters, commit=True)


class Packaging(Main):
    def __init__(self, english, korean, get_packagingid=False):
        self.english = english
        self.korean = korean
        self.get_packagingid = get_packagingid

    def register(self):
        if self.get_packagingid:
            SQL = "INSERT INTO packaging (english, korean) VALUES (%s,%s) RETURNING id;"
        else:
            SQL = "INSERT INTO packaging (english, korean) VALUES (%s,%s);"
        parameters = (self.english, self.korean,)
        return execute_query(query=SQL, parameters=parameters, commit=True, fetchOne=True)

    def update(self, id):
        SQL = "UPDATE packaging SET english = %s, korean = %s WHERE id = %s;"
        parameters = (
            self.english, self.korean, id,)
        execute_query(query=SQL, parameters=parameters, commit=True)


class PricesPackaging(Main):
    def __init__(self, packagingID, price_per_unit, date=None):
        self.packagingID = packagingID
        self.price_per_unit = price_per_unit
        self.date = date

    def register(self):
        if self.date == None:
            SQL = "INSERT INTO prices_packaging (packagingID, price_per_unit,date) VALUES (%s,%s,now());"
            parameters = (self.packagingID, self.price_per_unit,)
        else:
            SQL = "INSERT INTO prices_packaging (packagingID, price_per_unit,date) VALUES (%s,%s,%s);"
            parameters = (self.packagingID, self.price_per_unit, self.date,)
        execute_query(query=SQL, parameters=parameters, commit=True)

    def update(self, id):
        if self.date == None:
            SQL = "UPDATE prices_packaging SET packagingID = %s, price_per_unit = %s WHERE id = %s;"
            parameters = (self.packagingID, self.price_per_unit, id,)
        else:
            SQL = "UPDATE prices_packaging SET packagingID = %s, price_per_unit = %s, date = %s WHERE id = %s;"
            parameters = (self.packagingID, self.price_per_unit, self.date, id,)
        execute_query(query=SQL, parameters=parameters, commit=True)


class Products(Main):
    def __init__(self, english, korean, weight_in_gram_per_product, unit, image, type, currently_selling, best,
                 korean_description, english_description, qr, selling_price_lv, criteria_lv, selling_price_mv,
                 criteria_mv, selling_price_hv, criteria_hv, work_time_min, estimated_items):
        self.english = english
        self.korean = korean
        self.weight_in_gram_per_product = weight_in_gram_per_product
        self.unit = unit
        self.image = image
        self.type = type
        self.currently_selling = currently_selling
        self.best = best
        self.korean_description = korean_description
        self.english_description = english_description
        self.qr = qr
        self.selling_price_lv = selling_price_lv
        self.criteria_lv = criteria_lv
        self.selling_price_mv = selling_price_mv
        self.criteria_mv = criteria_mv
        self.selling_price_hv = selling_price_hv
        self.criteria_hv = criteria_hv
        self.work_time_min = work_time_min
        self.estimated_items = estimated_items

    def register(self):
        SQL = "INSERT INTO products (english, korean, weight_in_gram_per_product, unit, image, type, currently_selling, best, korean_description, english_description, qr, selling_price_lv, criteria_lv, selling_price_mv, criteria_mv, selling_price_hv, criteria_hv, work_time_min, estimated_items) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) returning id;"
        parameters = (self.english, self.korean, self.weight_in_gram_per_product, self.unit, self.image, self.type,
                      self.currently_selling, self.best, self.korean_description, self.english_description, self.qr,
                      self.selling_price_lv, self.criteria_lv, self.selling_price_mv, self.criteria_mv,
                      self.selling_price_hv, self.criteria_hv, self.work_time_min, self.estimated_items)
        return execute_query(query=SQL, parameters=parameters, commit=True, fetchOne=True)

    def update(self, id):
        SQL = "UPDATE products SET english = %s, korean = %s, weight_in_gram_per_product = %s, unit = %s, image = %s, type = %s, currently_selling = %s, best = %s, korean_description = %s, english_description = %s, qr = %s, selling_price_lv = %s, criteria_lv = %s, selling_price_mv = %s, criteria_mv = %s, selling_price_hv = %s, criteria_hv = %s, work_time_min = %s, estimated_items = %s WHERE id = %s;"
        parameters = (self.english, self.korean, self.weight_in_gram_per_product, self.unit, self.image, self.type,
                      self.currently_selling, self.best, self.korean_description, self.english_description, self.qr,
                      self.selling_price_lv, self.criteria_lv, self.selling_price_mv, self.criteria_mv,
                      self.selling_price_hv, self.criteria_hv, self.work_time_min, self.estimated_items, id,)
        execute_query(query=SQL, parameters=parameters, commit=True)


class IngredientProduct(Main):
    def __init__(self, productID, ingredientID, weight_in_gram):
        self.productID = productID
        self.ingredientID = ingredientID
        self.weight_in_gram = weight_in_gram

    def register(self):
        SQL = "INSERT INTO ingredientproduct (productID, ingredientID, weight_in_gram) VALUES (%s,%s,%s);"
        parameters = (self.productID, self.ingredientID, self.weight_in_gram,)
        execute_query(query=SQL, parameters=parameters, commit=True)

    def update(self, id):
        SQL = "UPDATE ingredientproduct SET productID = %s, ingredientID = %s, weight_in_gram = %s WHERE id = %s;"
        parameters = (self.productID, self.ingredientID, self.weight_in_gram, id,)
        execute_query(query=SQL, parameters=parameters, commit=True)


class PackagingProduct(Main):
    def __init__(self, productID, packagingID):
        self.productID = productID
        self.packagingID = packagingID

    def register(self):
        SQL = "INSERT INTO packagingproduct (productID, packagingID) VALUES (%s,%s);"
        parameters = (self.productID, self.packagingID,)
        execute_query(query=SQL, parameters=parameters, commit=True)

    def update(self, id):
        SQL = "UPDATE packagingproduct SET productID = %s, packagingID = %s WHERE id = %s;"
        parameters = (self.productID, self.packagingID, id,)
        execute_query(query=SQL, parameters=parameters, commit=True)


class InvoicesSupplier(Main):
    def __init__(self, file, type, payment_amount, payment_method, supplier_name, invoice_date):
        self.file = file
        self.type = type
        self.payment_amount = payment_amount
        self.payment_method = payment_method
        self.supplier_name = supplier_name
        self.invoice_date = invoice_date

    def register(self):
        SQL = "INSERT INTO invoices_suppliers (file, type, payment_amount, payment_method, supplier_name, invoice_date) VALUES (%s,%s,%s,%s,%s,%s);"
        parameters = (
            self.file, self.type, self.payment_amount, self.payment_method, self.supplier_name, self.invoice_date,)
        execute_query(query=SQL, parameters=parameters, commit=True)

    def update(self, id):
        SQL = "UPDATE invoices_suppliers SET file = %s, type = %s, payment_amount = %s, payment_method = %s, supplier_name = %s , invoice_date = %s WHERE id = %s;"
        parameters = (
            self.file, self.type, self.payment_amount, self.payment_method, self.supplier_name, self.invoice_date, id,)
        execute_query(query=SQL, parameters=parameters, commit=True)


class InvoicesCustomer(Main):
    def __init__(self, file, type, payment_amount, payment_method, customer_name, invoice_date):
        self.file = file
        self.type = type
        self.payment_amount = payment_amount
        self.payment_method = payment_method
        self.customer_name = customer_name
        self.invoice_date = invoice_date

    def register(self):
        SQL = "INSERT INTO invoices_customers (file, type, payment_amount, payment_method, customer_name, invoice_date) VALUES (%s,%s,%s,%s,%s,%s);"
        parameters = (
            self.file, self.type, self.payment_amount, self.payment_method, self.customer_name, self.invoice_date,)
        execute_query(query=SQL, parameters=parameters, commit=True)

    def update(self, id):
        SQL = "UPDATE invoices_customers SET file = %s, type = %s, payment_amount = %s, payment_method = %s, customer_name = %s , invoice_date = %s WHERE id = %s;"
        parameters = (
            self.file, self.type, self.payment_amount, self.payment_method, self.customer_name, self.invoice_date, id,)
        execute_query(query=SQL, parameters=parameters, commit=True)


class WebTranslations(Main):
    def __init__(self, msgid, korean, english):
        self.msgid = msgid
        self.english = english
        self.korean = korean

    def register(self):
        SQL = "INSERT INTO web_translations (msgid, korean, english) VALUES (%s,%s,%s);"
        parameters = (self.msgid, self.korean, self.english,)
        execute_query(query=SQL, parameters=parameters, commit=True)

    def update(self, id):
        SQL = "UPDATE web_translations SET msgid = %s, korean = %s, english = %s WHERE id = %s;"
        parameters = (self.msgid, self.korean, self.english, id,)
        execute_query(query=SQL, parameters=parameters, commit=True)


class RecipeComments(Main):
    def __init__(self, productid, comment):
        self.productid = productid
        self.comment = comment

    def register(self):
        SQL = "INSERT INTO recipe_comments (productid, comment) VALUES (%s,%s);"
        parameters = (self.productid, self.comment,)
        execute_query(query=SQL, parameters=parameters, commit=True)

    def update(self, id):
        SQL = "UPDATE recipe_comments SET productid = %s, comment = %s WHERE id = %s;"
        parameters = (
            self.productid, self.comment, id,)
        execute_query(query=SQL, parameters=parameters, commit=True)


class RegisterAllergensProduct(Main):
    def __init__(self, product_dict):
        self.product_dict = product_dict
        self.allergen_list = []
        for productid in self.product_dict:
            for allergen_product in [(productid, key, productid[key]) for key in productid]:
                self.allergen_list = self.allergen_list + str(allergen_product) + ', '
                # self.allergen_list = self.allergen_list + str(allergen_product) + ', '
        for x in self.allergen_list:
            print(x)

    def register_allergens_per_product(self):
        SQL = f"INSERT INTO allergenproduct (productID, AllergenID, contains_allergen) VALUES {self.allergen_list};"
        execute_query(query=SQL, commit=True)


class AllergenProduct(Main):
    def __init__(self, productID, AllergenID, contains_allergen):
        self.productID = productID
        self.AllergenID = AllergenID
        self.contains_allergen = contains_allergen

    def register(self):
        SQL = f"INSERT INTO allergenproduct (productID, AllergenID, contains_allergen) VALUES (%s,%s,%s);"
        parameters = (self.productID, self.AllergenID, self.contains_allergen,)
        execute_query(query=SQL, parameters=parameters, commit=True)

    def update(self):
        SQL = "UPDATE allergenproduct SET contains_allergen= %s WHERE productID = %s AND AllergenID = %s;"
        parameters = (self.contains_allergen, self.productID, self.AllergenID,)
        execute_query(query=SQL, parameters=parameters, commit=True)


class News(Main):
    def __init__(self, english_news_title, korean_news_title, english_news_subtitle, korean_news_subtitle,
                 english_news_details, korean_news_details, lightbox_image, display_image, active, bs_interval,
                 is_published):
        self.english_news_title = english_news_title
        self.korean_news_title = korean_news_title
        self.english_news_subtitle = english_news_subtitle
        self.korean_news_subtitle = korean_news_subtitle
        self.english_news_details = english_news_details
        self.korean_news_details = korean_news_details
        self.lightbox_image = lightbox_image
        self.display_image = display_image
        self.active = active
        self.bs_interval = bs_interval
        self.is_published = is_published

    def register(self):
        SQL = f"INSERT INTO news (english_news_title, korean_news_title, english_news_subtitle, korean_news_subtitle, english_news_details, korean_news_details, lightbox_image, display_image, active, bs_interval, is_published) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
        parameters = (
            self.english_news_title, self.korean_news_title, self.english_news_subtitle, self.korean_news_subtitle,
            self.english_news_details, self.korean_news_details, self.lightbox_image, self.display_image, self.active,
            self.bs_interval, self.is_published,)
        execute_query(query=SQL, parameters=parameters, commit=True)

    def update(self, news_id):
        SQL = "UPDATE news SET english_news_title= %s, korean_news_title= %s, english_news_subtitle= %s, korean_news_subtitle= %s, english_news_details= %s, korean_news_details= %s, lightbox_image= %s, display_image= %s, active= %s, bs_interval= %s, is_published = %s  WHERE id = %s;"
        parameters = (
            self.english_news_title, self.korean_news_title, self.english_news_subtitle, self.korean_news_subtitle,
            self.english_news_details, self.korean_news_details, self.lightbox_image, self.display_image, self.active,
            self.bs_interval, self.is_published, news_id,)
        execute_query(query=SQL, parameters=parameters, commit=True)


class Sale(Main):
    def __init__(self, date, amount_low, price_low_amount, amount_medium, price_medium_amount, amount_high,
                 price_high_amount, product_id, variable_cost, total_income, VAT):
        self.date = date
        self.amount_low = amount_low
        self.price_low_amount = price_low_amount
        self.amount_medium = amount_medium
        self.price_medium_amount = price_medium_amount
        self.amount_high = amount_high
        self.price_high_amount = price_high_amount
        self.product_id = product_id
        self.variable_cost = variable_cost
        self.total_income = total_income
        self.VAT = VAT

    def register(self):
        if self.date == None:
            SQL = f"INSERT INTO sales (date, amount_low, price_low_amount, amount_medium, price_medium_amount, amount_high, price_high_amount, product_id, variable_cost, total_income, VAT) VALUES (NOW(),%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
            parameters = (self.amount_low, self.price_low_amount, self.amount_medium, self.price_medium_amount,
                self.amount_high, self.price_high_amount, self.product_id, self.variable_cost, self.total_income,
                self.VAT,)
        else:
            SQL = f"INSERT INTO sales (date, amount_low, price_low_amount, amount_medium, price_medium_amount, amount_high, price_high_amount, product_id, variable_cost, total_income, VAT) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);"
            parameters = (
                self.date, self.amount_low, self.price_low_amount, self.amount_medium, self.price_medium_amount,
                self.amount_high, self.price_high_amount, self.product_id, self.variable_cost, self.total_income,
                self.VAT,)
        execute_query(query=SQL, parameters=parameters, commit=True)

    def update(self, sale_id):
        if self.date == None:
            SQL = "UPDATE sales SET date = NOW(), amount_low = %s, price_low_amount = %s, amount_medium = %s, price_medium_amount = %s, amount_high = %s, price_high_amount = %s, product_id = %s, variable_cost = %s, total_income = %s, VAT = %s  WHERE id = %s;"
            parameters = (
                self.amount_low, self.price_low_amount, self.amount_medium, self.price_medium_amount,
                self.amount_high, self.price_high_amount, self.product_id, self.variable_cost, self.total_income,
                self.VAT, sale_id,)
        else:
            SQL = "UPDATE sales SET date = %s, amount_low = %s, price_low_amount = %s, amount_medium = %s, price_medium_amount = %s, amount_high = %s, price_high_amount = %s, product_id = %s, variable_cost = %s, total_income = %s, VAT = %s  WHERE id = %s;"
            parameters = (
                self.date, self.amount_low, self.price_low_amount, self.amount_medium, self.price_medium_amount,
                self.amount_high, self.price_high_amount, self.product_id, self.variable_cost, self.total_income, self.VAT, sale_id,)
        execute_query(query=SQL, parameters=parameters, commit=True)
