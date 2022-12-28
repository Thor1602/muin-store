# This Python file uses the following encoding: utf-8
import datetime
import Database

main = Database.Main()
print(datetime.datetime.now())
Database.open_connection()
# do stuff


Database.close_connection()
# do stuff


print(datetime.datetime.now())

