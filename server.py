import datetime
import decimal
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import mysql.connector
from urllib.parse import urlparse, parse_qs
from hashlib import sha256
import http.cookies
import urllib
import jwt

# Database configuration
db_config = {
    "user": "root",
    "password": "root",
    "host": "localhost",
    "port": 3306,
    "database": "gharbahal",
}


# Establish database connection
def get_db_connection():
    return mysql.connector.connect(**db_config)


class RequestHandler(BaseHTTPRequestHandler):

    def _set_headers(self, status_code=200, content_type="text/plain"):
        self.send_response(status_code)
        self.send_header("Content-type", content_type)
        self.send_header("Access-Control-Allow-Origin", "http://localhost:5500")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers()

    def do_GET(self):

        if self.path == "/":
            self._set_headers(content_type="text/html")
            with open("static/dashboard/basiclayout.html", "r") as file:
                html_content = file.read()
            self.wfile.write(html_content.encode("utf-8"))

        elif self.path.startswith("/api/properties"):
            self._set_headers(content_type="application/json")
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            page = int(params.get("page", [1])[0])
            page_size = int(params.get("page_size", [10])[0])
            data = self.get_properties_from_db(page, page_size)
            self.wfile.write(json.dumps(data).encode("utf-8"))

        elif self.path == ("/api/trending"):
            self._set_headers(content_type="application/json")
            page = 1
            page_size = 6
            data = self.get_trending_from_db(page, page_size)
            self.wfile.write(json.dumps(data).encode("utf-8"))

        elif self.path == ("/api/recommended"):
            self._set_headers(content_type="application/json")
            page = 1
            page_size = 6
            data = self.get_recommended_from_db(page, page_size)
            self.wfile.write(json.dumps(data).encode("utf-8"))

        elif self.path == ("/api/recents"):
            self._set_headers(content_type="application/json")
            page = 1
            page_size = 6
            data = self.get_recents_from_db(page, page_size)
            self.wfile.write(json.dumps(data).encode("utf-8"))

        elif self.path == "/login":
            self._set_headers(content_type="text/html")
            with open("static/loginpage/login.html", "r") as file:
                html_content = file.read()
            self.wfile.write(html_content.encode("utf-8"))

        elif self.path == "/register":
            self._set_headers(content_type="text/html")
            with open("static/loginpage/register.html", "r") as file:
                html_content = file.read()
            self.wfile.write(html_content.encode("utf-8"))

        elif self.path.startswith("/api/details"):
            self._set_headers(content_type="text/html")
            with open("static/details/propertydetails.html", "r") as file:
                html_content = file.read()
            self.wfile.write(html_content.encode("utf-8"))

        elif self.path == "/api/checktoken":
            print(f"this is headers {self.headers}")
            token = self.headers.get("Authorization")
            if token:
                token = token.split(" ")[1]  # Assuming 'Bearer <token>'
                token_data = self.decode_token(token)
                if token_data.get("error"):
                    success = False
                    message = token_data.get("message")
                else:
                    success = True
                    message = None

                data = {"success": success, "data": token_data, "message": message}
                response = json.dumps(data)
            else:
                response = json.dumps(
                    {"success": False, "message": "Authorization header not found"}
                )
            self._set_headers(200, content_type="application/json")
            self.wfile.write(response.encode("utf-8"))

        else:
            self._set_headers(content_type="text/html")
            with open("static/pagenotfound/pagenotfound.html", "r") as file:
                html_content = file.read()
            self.wfile.write(html_content.encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)

        # self._set_headers(content_type='application/json')

        if self.path == "/api/register":
            email = data.get("email")
            password = data.get("password")
            username = data.get("username")
            role = data.get("role")
            if email and password and username and role:
                if role.lower() == "admin":
                    self.send_response(401)
                    response = {"error": "cannot create admin from here."}
                    self.wfile.write(json.dumps(response).encode("utf-8"))

                hashed_password = sha256(password.encode("utf-8")).hexdigest()

                connection = get_db_connection()
                cursor = connection.cursor()

                try:
                    cursor.execute(
                        "INSERT INTO users (username,email, password, role) VALUES (%s,%s,%s, %s)",
                        (username, email, hashed_password, role),
                    )
                    connection.commit()
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    response = {
                        "message": "User registered successfully",
                        "success": True,
                    }
                    self.wfile.write(json.dumps(response).encode("utf-8"))
                except mysql.connector.Error as err:
                    print(str(e))
                    self.send_response(401)
                    response = {"error": str(err)}
                    self.wfile.write(json.dumps(response).encode("utf-8"))
                except Exception as e:
                    print(str(Exception))
                finally:
                    cursor.close()
                    connection.close()

        elif self.path == "/api/login":
            username = data.get("username")
            password = data.get("password")
            if username and password:
                hashed_password = sha256(password.encode("utf-8")).hexdigest()

                connection = get_db_connection()
                cursor = connection.cursor()

                try:
                    cursor.execute(
                        "SELECT password FROM users WHERE username = %s", (username,)
                    )
                    result = cursor.fetchone()
                    if result and result[0] == hashed_password:
                        print("Login successful for user:", username)
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        response = {
                            "message": "Login successful",
                            "token": self.generate_token_for_user(username),
                            "success": True,
                        }
                        print(response)
                        self.wfile.write(json.dumps(response).encode("utf-8"))
                    else:
                        self.send_response(401)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        response = {
                            "message": "Invalid email or password",
                            "success": False,
                        }
                        self.wfile.write(json.dumps(response).encode("utf-8"))
                except mysql.connector.Error as err:
                    print("Database error:", str(err))
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    response = {"error": str(err), "success": False}
                    self.wfile.write(json.dumps(response).encode("utf-8"))
                finally:
                    cursor.close()
                    connection.close()
            else:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                response = {
                    "message": "Email and password are required",
                    "success": False,
                }
                self.wfile.write(json.dumps(response).encode("utf-8"))

        else:
            self.send_response(404)
            response = {"message": "Not Found"}
            self.wfile.write(json.dumps(response).encode("utf-8"))

    def get_trending_from_db(self, page=1, page_size=6):
        try:
            offset = (page - 1) * page_size
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            order_by = "-views"
            cursor.execute(
                f"SELECT id, title, description, price,status, address, city, state, zip_code FROM properties ORDER BY {order_by} LIMIT {page_size} OFFSET {offset}"
            )
            properties = cursor.fetchall()
            for property in properties:
                for key, value in property.items():
                    if isinstance(value, decimal.Decimal):
                        property[key] = float(value)
            cursor.close()
            connection.close()
            return {"properties": properties}
        except Exception as e:
            print(str(e))
            return None

    def get_recommended_from_db(self, page=1, page_size=6):
        try:
            offset = (page - 1) * page_size
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            order_by = "created_at"
            cursor.execute(
                f"SELECT id, title, description, price,status, address, city, state, zip_code FROM properties ORDER BY {order_by} LIMIT {page_size} OFFSET {offset}"
            )
            properties = cursor.fetchall()
            for property in properties:
                for key, value in property.items():
                    if isinstance(value, decimal.Decimal):
                        property[key] = float(value)
            cursor.close()
            connection.close()
            return {"properties": properties}
        except Exception as e:
            print(str(e))
            return None

    def get_recents_from_db(self, page=1, page_size=6):
        try:
            offset = (page - 1) * page_size
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            order_by = "-created_at"
            cursor.execute(
                f"SELECT id, title, description, price,status, address, city, state, zip_code FROM properties ORDER BY {order_by} LIMIT {page_size} OFFSET {offset}"
            )
            properties = cursor.fetchall()
            for property in properties:
                for key, value in property.items():
                    if isinstance(value, decimal.Decimal):
                        property[key] = float(value)
            cursor.close()
            connection.close()
            return {"properties": properties}
        except Exception as e:
            print(str(e))
            return None

    def get_properties_from_db(self, page=1, page_size=10):
        try:
            offset = (page - 1) * page_size
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT id, title, description, price, address, city, state, zip_code FROM properties LIMIT %s OFFSET %s",
                (page_size, offset),
            )
            properties = cursor.fetchall()
            for property in properties:
                for key, value in property.items():
                    if isinstance(value, decimal.Decimal):
                        property[key] = float(value)
            cursor.close()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as count FROM properties")
            total_count = cursor.fetchone()["count"]
            cursor.close()
            connection.close()
            return {
                "properties": properties,
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
            }
        except Exception as e:
            print(str(e))
            return None

    def generate_token_for_user(self, username):
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "Select id, role, username FROM users where username = %s", (username,)
            )
            result = cursor.fetchone()
            payload = {
                "user_id": result["id"],
                "username": result["username"],
                "role": result["role"],
                "exp": datetime.datetime.now() + datetime.timedelta(minutes=480),
            }
            token = jwt.encode(payload, "secret_key", "HS256")
            return token
        except Exception as e:
            print(str(e))
            return None

    def decode_token(self, token):
        try:
            decoded = jwt.decode(token, "secret_key", "HS256")
            if decoded:
                user_id = decoded.get("user_id")
                exp = decoded.get("exp")
                username = decoded.get("username")
                role = decoded.get("role")
                return {
                    "user_id": user_id,
                    "exp": exp,
                    "username": username,
                    "role": role,
                }
        except jwt.ExpiredSignatureError:
            return {"error": True, "message": "Session expired. Please Relogin"}
        except jwt.InvalidTokenError:
            return {"error": True, "message": "Invalid Request. Please Login"}
        except Exception:
            return {"error": True, "message": "Server Error"}


def run():
    server_address = ("", 7000)
    httpd = HTTPServer(server_address, RequestHandler)
    print("Server is running at http://localhost:7000")
    httpd.serve_forever()


if __name__ == "__main__":
    run()
