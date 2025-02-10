import mysql.connector

# Replace these values with your own MySQL server details
host = "localhost"
user = "mcash_python"
password = "mcash_python"
database = "mcash_python"
#mysql+pymysql://remit_admin:remit_admin@localhost/remit

# Establish a connection to the MySQL database
try:
    connection = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )

    if connection.is_connected():
        print("Successfully connected to the database")

except mysql.connector.Error as err:
    print(f"Error: {err}")

finally:
    if connection.is_connected():
        connection.close()
        print("Connection closed")
