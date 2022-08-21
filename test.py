import psycopg2.errors
from psycopg2.errorcodes import UNIQUE_VIOLATION

import Database

main = Database.Main()
# main.execute_query(query_list="CREATE TABLE quiz (id serial PRIMARY KEY, name varchar);", commit=True)
# main.execute_query(query_list="CREATE TABLE usercourse (id serial PRIMARY KEY, userID integer references users(id), CourseID integer references course(id));", commit=True)
# main.execute_query(query_list="CREATE TABLE question (id serial PRIMARY KEY, quizID integer references quiz(id), question varchar, answer_one varchar, answer_two varchar, answer_three varchar, answer_four varchar, correct_answer varchar);", commit=True)
# main.execute_query(query_list="CREATE TABLE translationkoreng (id serial PRIMARY KEY, Korean varchar, English varchar);", commit=True)
# main.execute_query(query_list="CREATE TABLE grades (id serial PRIMARY KEY, courseID integer references course(id),quizID integer references quiz(id),userID integer references users(id), score integer, total_score integer);", commit=True)
# main.execute_query(query_list="CREATE TABLE discussion (id serial PRIMARY KEY, topic varchar, date timestamp, userID integer references users(id), image_id integer, question varchar);", commit=True)
# main.execute_query(query_list="CREATE TABLE reply (id serial PRIMARY KEY, reply varchar, date timestamp, postID integer references post(id), userID integer references users(id));", commit=True)
# main.execute_query(query_list="CREATE TABLE subreply (id serial PRIMARY KEY, subreply varchar, date timestamp, replyID integer references reply(id), userID integer references users(id));", commit=True)
# main.execute_query(query_list="INSERT INTO users (first_name,last_name,nickname,password,role_name,email,last_login,created_on) VALUES ('Thorben', 'Dhaenens', 'Thor Administrator', '" + main.generate_hash("23FvMIs*5cx8fHRv") + "', 'Administrator', 'thorbendhaenenstd@gmail.com',NOW(),NOW());", commit=True)
# main.execute_query(query_list="INSERT INTO users (first_name,last_name,nickname,password,role_name,email,last_login,created_on) VALUES ('Tester', 'Handy', 'Test member', '" + main.generate_hash("123honey") + "', 'Member', 'test@gmail.com',NOW(),NOW());", commit=True)
# print(main.verify_password("thorbendhaenenstd@gmail.com", "3%iygp4yYeJ9E8Dpu&oQ$GP$vVc"))
# main.execute_query("ALTER TABLE quiz ADD CONSTRAINT constraintOne UNIQUE (name);", commit=True)
# main.add_column('grades', 'date', 'timestamp')
# for x in main.read_columns('translationkoreng'):
#     print(x[0])
# print(main.read_columns('translationkoreng'))
print("answer_"[:6])
# quiz = Database.Quiz("postpositions")
# quiz.register_quiz

