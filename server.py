import datetime
import decimal
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import mimetypes
import string
from threading import Timer
import mysql.connector
from urllib.parse import urlparse, parse_qs
from hashlib import sha256
import urllib
import jwt
import os
import cgi
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Database configuration
db_config = {
    "user": "root",
    "password": "root",
    "host": "localhost",
    "port": 3306,
    "database": "gharbahal",
}


def send_email(recipient_email, subject, body):
    # Setup the MIME
    sender_email = "gharbahaal@gmail.com"
    sender_password = "ncbu orbh abfy gxhs"
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = subject

    # Add body to email
    message.attach(MIMEText(body, "plain"))

    try:
        # Connect to the server
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Enable security
            server.login(sender_email, sender_password)  # Login to the SMTP server
            text = message.as_string()  # Convert the message to a string
            server.sendmail(sender_email, recipient_email, text)  # Send the email
            print("Email sent successfully!")
    except Exception as e:
        print(f"An error occurred: {e}")


# Establish database connection
def get_db_connection():
    print("success")
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

        elif self.path.startswith("/api/checkreviewstatus"):
            print(self.headers)
            product_id = int(str(self.headers.get("product_id")))
            connection = get_db_connection()
            cursor = connection.cursor()
            token = self.headers.get("Authorization").split(" ")[1]
            verify = self.decode_token(token)
            if verify.get("error"):
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = {"success": False, "message": "Token not found or expired"}
                self.wfile.write(json.dumps(response).encode("utf-8"))
            else:
                user_id = verify.get("user_id")
                cursor.execute(
                    "Select * from reviews where property_id = %s and tenant_id = %s",
                    (
                        product_id,
                        user_id,
                    ),
                )
                result = cursor.fetchone()
                if result:
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    response = {"success": True, "message": "Review already exists"}
                    self.wfile.write(json.dumps(response).encode("utf-8"))
                else:
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    response = {"success": False, "message": "Can post review"}
                    self.wfile.write(json.dumps(response).encode("utf-8"))

        elif self.path.startswith("/api/properties"):
            self._set_headers(content_type="application/json")
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            page = int(params.get("page", [1])[0])
            page_size = int(params.get("page_size", [10])[0])
            data = self.get_properties_from_db(page, page_size)
            self.wfile.write(json.dumps(data).encode("utf-8"))

        elif self.path.startswith("/api/analytics"):
            self._set_headers(content_type="application/json")
            token = self.headers.get("Authorization").split(" ")[1]
            verify = self.decode_token(token)
            if verify.get("error"):
                error = {"success": False, "message": "Please Login"}
                self.wfile.write(json.dumps(error).encode("utf-8"))
            userid = verify.get("user_id")
            data = {"success": True, "data": self.getAnalytics(userid)}
            self.wfile.write(json.dumps(data).encode("utf-8"))

        elif self.path.startswith("/api/savedlist"):
            self._set_headers(content_type="application/json")
            token = self.headers.get("Authorization").split(" ")[1]
            verify = self.decode_token(token)
            if verify.get("error"):
                error = {"success": False, "message": "Please Login"}
                self.wfile.write(json.dumps(error).encode("utf-8"))
            else:
                userid = verify.get("user_id")
                data = {"success": True, "data": self.getSaved(userid)}
                self.wfile.write(json.dumps(data).encode("utf-8"))

        elif self.path.startswith("/api/userproducts"):
            self._set_headers(content_type="application/json")
            token = self.headers.get("Authorization").split(" ")[1]
            verify = self.decode_token(token)
            if verify.get("error"):
                error = {"success": False, "message": "Please Login"}
                self.wfile.write(json.dumps(error).encode("utf-8"))
            else:
                userid = verify.get("user_id")
                data = {"success": True, "data": self.getAllUserProperties(userid)}
                self.wfile.write(json.dumps(data).encode("utf-8"))

        elif self.path.startswith("/userprofile"):
            self._set_headers(content_type="text/html")
            userid = self.path.split("/")[-1]
            print(userid)
            with open("static/details/userprofile.html", "r") as file:
                html_content = file.read()
            self.wfile.write(html_content.encode("utf-8"))

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

        elif self.path.startswith("/api/editproperty"):
            self._set_headers(content_type="text/html")
            property_id = self.path.split("/")[-1]
            property_data, property_reviews = self.get_property_details(property_id)
            if property_data:
                html_content = self.render_property_edit_details(property_data)
                self.wfile.write(html_content.encode("utf-8"))
            else:
                with open("static/pagenotfound/pagenotfound.html", "r") as file:
                    html_content = file.read()
                self.wfile.write(html_content.encode("utf-8"))

        elif self.path.startswith("/api/details"):
            self._set_headers(content_type="text/html")
            property_id = self.path.split("/")[-1]
            property_data, property_reviews = self.get_property_details(property_id)

            if property_data:
                html_content = self.render_property_details(
                    property_data, property_reviews
                )
                self.wfile.write(html_content.encode("utf-8"))
            else:
                with open("static/pagenotfound/pagenotfound.html", "r") as file:
                    html_content = file.read()
                self.wfile.write(html_content.encode("utf-8"))
        elif self.path.startswith("/api/userproperty"):
            self._set_headers(content_type="text/html")
            property_id = self.path.split("/")[-1]
            property_data, property_reviews = self.get_property_details(property_id)

            if property_data:
                html_content = self.render_user_property_details(
                    property_data, property_reviews
                )
                self.wfile.write(html_content.encode("utf-8"))
            else:
                with open("static/pagenotfound/pagenotfound.html", "r") as file:
                    html_content = file.read()
                self.wfile.write(html_content.encode("utf-8"))

        elif self.path == "/addproduct":
            self._set_headers(content_type="text/html")
            with open("static/details/addproperty.html", "r") as file:
                html_content = file.read()
            self.wfile.write(html_content.encode("utf-8"))

        elif self.path == "/api/checktoken":
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

        elif self.path.startswith("/propertyimages/"):
            self._set_headers(
                content_type="image/jpeg"
            )  # Adjust content_type based on the image format
            image_path = self.path.lstrip("/")
            if os.path.exists(image_path):
                with open(image_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.wfile.write(b"Image not found")

        elif self.path.startswith("/searchproperty"):
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)

            property_type = query_params.get("type", [""])[0]
            city = query_params.get("city", [""])[0]

            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            search_city_like = f"%{city}%"
            cursor.execute(
                "SELECT * FROM properties WHERE city LIKE %s and type = %s",
                (search_city_like, property_type),
            )
            properties = cursor.fetchall()
            details = self.render_search_details(property_data=properties)
            self._set_headers(content_type="text/html")
            self.wfile.write(details.encode("utf-8"))

        elif self.path.startswith("/useravailables/"):
            try:
                userid = self.path.split("/")[-1]
                connection = get_db_connection()
                cursor = connection.cursor(dictionary=True)
                cursor.execute(
                    "SELECT * FROM properties WHERE status = 'available' AND owner_id = %s",
                    (userid,),
                )
                properties = cursor.fetchall()
                html_string = f""
                for property in properties:
                    print(property)
                    html_string += f"""
                    <div class="bg-violet-50 hover:bg-violet-200 min-h-96 max-h-96 cursor-pointer hov flex flex-col p-4 m-1 shadow-md rounded-md">
                        <div class="flex justify-between">
                            <h2 class="text-xl">{property['title']}</h2>
                            <p class="font-mono text-sm capitalize">{property['status']}</p>
                        </div>
                        <div class="py-2 flex justify-center items-center">
                            <img src="../../{property['thumbnail']}" class="object-cover min-h-44 max-h-44 w-full">
                        </div>
                        <small class="text-[16px] text-left">Buy it at NPR. <script>document.write(formatCustomNumber({property['price']}));</script></small>
                        <small class="capitalize text-left">Located in {property['street_name']}, {property['city']}, {property['state']}</small>
                        <small class="text-left capitalize"><script>document.write(truncateString('{property.get('description', '')}', 100, true));</script></small>
                        <a href="/api/details/{property['id']}" class="pt-2 text-center text-[14px] hover:underline underline-offset-2 hover:text-blue-800"> View More</a>
                    </div>
                    """
                with open("static/dashboard/userproperty.html", "r") as file:
                    html_content = file.read()
                html_content = html_content.replace("{{results}}", html_string)
                self._set_headers(content_type="text/html")
                self.end_headers()
                self.wfile.write(html_content.encode("utf-8"))

            except Exception as e:
                print(str(e))
                self._set_headers(content_type="text/html")
        elif self.path.startswith("/userallproperties/"):
            try:
                userid = self.path.split("/")[-1]
                connection = get_db_connection()
                cursor = connection.cursor(dictionary=True)
                cursor.execute(
                    "SELECT * FROM properties WHERE owner_id = %s", (userid,)
                )
                properties = cursor.fetchall()
                html_string = f""
                for property in properties:
                    print(property)
                    html_string += f"""
                    <div class="bg-violet-50 hover:bg-violet-200 min-h-96 max-h-96 cursor-pointer hov flex flex-col p-4 m-1 shadow-md rounded-md">
                        <div class="flex justify-between">
                            <h2 class="text-xl">{property['title']}</h2>
                            <p class="font-mono text-sm capitalize">{property['status']}</p>
                        </div>
                        <div class="py-2 flex justify-center items-center">
                            <img src="../../{property['thumbnail']}" class="object-cover min-h-44 max-h-44 w-full">
                        </div>
                        <small class="text-[16px] text-left">Buy it at NPR. <script>document.write(formatCustomNumber({property['price']}));</script></small>
                        <small class="capitalize text-left">Located in {property['street_name']}, {property['city']}, {property['state']}</small>
                        <small class="text-left capitalize"><script>document.write(truncateString('{property.get('description', '')}', 100, true));</script></small>
                        <a href="/api/details/{property['id']}" class="pt-2 text-center text-[14px] hover:underline underline-offset-2 hover:text-blue-800"> View More</a>
                    </div>
                    """
                with open("static/dashboard/userproperty.html", "r") as file:
                    html_content = file.read()
                html_content = html_content.replace("{{results}}", html_string)
                self._set_headers(content_type="text/html")
                self.end_headers()
                self.wfile.write(html_content.encode("utf-8"))

            except Exception as e:
                print(str(e))
                self._set_headers(content_type="text/html")

        elif self.path.startswith("/userrented/"):
            try:
                userid = self.path.split("/")[-1]
                connection = get_db_connection()
                cursor = connection.cursor(dictionary=True)
                cursor.execute(
                    "SELECT * FROM properties WHERE status = 'rented' AND tenant_id = %s",
                    (userid,),
                )
                html_string = f""
                properties = cursor.fetchall()
                if properties:
                    for property in properties:
                        print(property)
                        html_string += f"""
                        <div class="bg-violet-50 hover:bg-violet-200 min-h-96 max-h-96 cursor-pointer hov flex flex-col p-4 m-1 shadow-md rounded-md">
                            <div class="flex justify-between">
                                <h2 class="text-xl">{property['title']}</h2>
                                <p class="font-mono text-sm capitalize">{property['status']}</p>
                            </div>
                            <div class="py-2 flex justify-center items-center">
                                <img src="../../{property['thumbnail']}" class="object-cover min-h-44 max-h-44 w-full">
                            </div>
                            <small class="text-[16px] text-left">Buy it at NPR. <script>document.write(formatCustomNumber({property['price']}));</script></small>
                            <small class="capitalize text-left">Located in {property['street_name']}, {property['city']}, {property['state']}</small>
                            <small class="text-left capitalize"><script>document.write(truncateString('{property.get('description', '')}', 100, true));</script></small>
                            <a href="/api/details/{property['id']}" class="pt-2 text-center text-[14px] hover:underline underline-offset-2 hover:text-blue-800"> View More</a>
                            
                        </div>
                        """
                    with open("static/dashboard/userproperty.html", "r") as file:
                        html_content = file.read()
                    html_content = html_content.replace("{{results}}", html_string)
                    self._set_headers(content_type="text/html")
                    self.end_headers()
                    self.wfile.write(html_content.encode("utf-8"))
                else:
                    html_string += """<p class="text-bold text-lg">You do not have any rented properties</p>"""
                    with open("static/dashboard/userproperty.html", "r") as file:
                        html_content = file.read()
                    html_content = html_content.replace("{{results}}", html_string)
                    self._set_headers(content_type="text/html")
                    self.end_headers()
                    self.wfile.write(html_content.encode("utf-8"))

            except Exception as e:
                print(str(e))
                self._set_headers(content_type="text/html")

        elif self.path.startswith("/userrents/"):
            try:
                userid = self.path.split("/")[-1]
                connection = get_db_connection()
                cursor = connection.cursor(dictionary=True)
                cursor.execute(
                    "SELECT * FROM properties WHERE status = 'rented' AND owner_id = %s",
                    (userid,),
                )
                properties = cursor.fetchall()
                html_string = f""
                for property in properties:
                    print(property)
                    html_string += f"""
                    <div class="bg-violet-50 hover:bg-violet-200 min-h-96 max-h-96 cursor-pointer hov flex flex-col p-4 m-1 shadow-md rounded-md">
                        <div class="flex justify-between">
                            <h2 class="text-xl">{property['title']}</h2>
                            <p class="font-mono text-sm capitalize">{property['status']}</p>
                        </div>
                        <div class="py-2 flex justify-center items-center">
                            <img src="../../{property['thumbnail']}" class="object-cover min-h-44 max-h-44 w-full">
                        </div>
                        <small class="text-[16px] text-left">Buy it at NPR. <script>document.write(formatCustomNumber({property['price']}));</script></small>
                        <small class="capitalize text-left">Located in {property['street_name']}, {property['city']}, {property['state']}</small>
                        <small class="text-left capitalize"><script>document.write(truncateString('{property.get('description', '')}', 100, true));</script></small>
                        <a href="/api/details/{property['id']}" class="pt-2 text-center text-[14px] hover:underline underline-offset-2 hover:text-blue-800"> View More</a>
                        <div class="p-2">
                        <button data="{property['id']}" id="availablebutton" onclick="makeavailable()" class="rounded-md hover:cursor-pointer hover:text-white hover:bg-green-500 text-green-500 text-lg">Make it Available</a>
                        </div>
                    </div>
                    """
                with open("static/dashboard/userproperty.html", "r") as file:
                    html_content = file.read()
                html_content = html_content.replace("{{results}}", html_string)
                self._set_headers(content_type="text/html")
                self.end_headers()
                self.wfile.write(html_content.encode("utf-8"))

            except Exception as e:
                print(str(e))
                self._set_headers(content_type="text/html")

        elif self.path.startswith("/booked/"):
            try:
                userid = self.path.split("/")[-1]
                connection = get_db_connection()
                cursor = connection.cursor(dictionary=True)
                cursor.execute(
                    "SELECT * FROM properties WHERE status = 'booked' AND tenant_id = %s",
                    (userid,),
                )
                properties = cursor.fetchall()
                print(len(properties))
                html_string = f""
                if properties:
                    for property in properties:
                        print("\n")
                        html_string += f"""
                        <div class="property bg-violet-50 hover:bg-violet-200 min-h-96 max-h-96 cursor-pointer hov flex flex-col p-4 m-1 shadow-md rounded-md">
                            <div class="flex justify-between">
                                <h2 class="text-xl">{property['title']}</h2>
                                <p class="font-mono text-sm capitalize">{property['status']}</p>
                            </div>
                            <div class="py-2 flex justify-center items-center">
                                <img src="../../{property['thumbnail']}" class="object-cover min-h-44 max-h-44 w-full">
                            </div>
                            <small class="text-[16px] text-left">Buy it at NPR. {property['price']}</small>
                            <small class="capitalize text-left">Located in {property['street_name']}, {property['city']}, {property['state']}</small>
                            <small class="text-left capitalize">{property.get('description')}</small>
                            <a href="/api/userproperty/{property['id']}" class="pt-2 text-center text-[14px] hover:underline underline-offset-2 hover:text-blue-800"> View More</a>
                        </div>
                        """
                    with open("static/dashboard/userproperty.html", "r") as file:
                        html_content = file.read()
                    html_content = html_content.replace("{{results}}", html_string)
                    self._set_headers(content_type="text/html")
                    self.end_headers()
                    self.wfile.write(html_content.encode("utf-8"))
                else:
                    html_string = """
                    
                    <p class="text-bold text-lg"> You do not have any booked properties</p>
                    
                    """
                    with open("static/dashboard/userproperty.html", "r") as file:
                        html_content = file.read()
                    html_content = html_content.replace("{{results}}", html_string)
                    self._set_headers(content_type="text/html")
                    self.end_headers()
                    self.wfile.write(html_content.encode("utf-8"))

            except Exception as e:
                print(str(e))
                self._set_headers(content_type="text/html")

        elif self.path.startswith("/userbooked/"):
            try:
                userid = self.path.split("/")[-1]
                connection = get_db_connection()
                cursor = connection.cursor(dictionary=True)
                cursor.execute(
                    "SELECT * FROM properties WHERE status = 'booked' AND owner_id = %s",
                    (userid,),
                )
                properties = cursor.fetchall()
                print(len(properties))
                html_string = f""
                for property in properties:
                    print("\n")
                    html_string += f"""
                    <div class="property bg-violet-50 hover:bg-violet-200 min-h-96 max-h-96 cursor-pointer hov flex flex-col p-4 m-1 shadow-md rounded-md">
                        <div class="flex justify-between">
                            <h2 class="text-xl">{property['title']}</h2>
                            <p class="font-mono text-sm capitalize">{property['status']}</p>
                        </div>
                        <div class="py-2 flex justify-center items-center">
                            <img src="../../{property['thumbnail']}" class="object-cover min-h-44 max-h-44 w-full">
                        </div>
                        <small class="text-[16px] text-left">Buy it at NPR. {property['price']}</small>
                        <small class="capitalize text-left">Located in {property['street_name']}, {property['city']}, {property['state']}</small>
                        <small class="text-left capitalize">{property.get('description')}</small>
                        <a href="/api/userproperty/{property['id']}" class="pt-2 text-center text-[14px] hover:underline underline-offset-2 hover:text-blue-800"> View More</a>
                        <div class="flex justify-between py-4">
                        <button data="{property['id']}" id="rentbutton" onclick="makerent()" class="rounded-md hover:cursor-pointer hover:text-white hover:bg-green-500 text-green-500 text-lg">Approve for Rent</button>
                        <button data="{property['id']}" id="availablebutton" onclick="makeavailable()" class="rounded-md hover:cursor-pointer hover:text-white hover:bg-green-500 text-green-500 text-lg">Make it Available</a>

                        </div>
                    </div>
                    """
                with open("static/dashboard/userproperty.html", "r") as file:
                    html_content = file.read()
                html_content = html_content.replace("{{results}}", html_string)
                self._set_headers(content_type="text/html")
                self.end_headers()
                self.wfile.write(html_content.encode("utf-8"))

            except Exception as e:
                print(str(e))
                self._set_headers(content_type="text/html")

        else:
            self._set_headers(content_type="text/html")
            with open("static/pagenotfound/pagenotfound.html", "r") as file:
                html_content = file.read()
            self.wfile.write(html_content.encode("utf-8"))

    def do_POST(self):

        # self._set_headers(content_type='application/json')

        if self.path == "/api/register":
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            email = data.get("email")
            password = data.get("password")
            username = data.get("username")
            number = data.get("number")
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
                        "INSERT INTO users (username,number,email, password, role) VALUES (%s,%s,%s,%s, %s)",
                        (username, number, email, hashed_password, role),
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

        elif self.path.startswith("/api/makerent"):
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            property_id = data.get("property_id")
            token = self.headers.get("Authorization").split(" ")[1]
            verify = self.decode_token(token)
            if verify.get("error"):
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = {"success": False, "message": "token missing"}
                self.wfile.write(json.dumps(response).encode("utf-8"))
            else:
                status = "rented"
                connection = get_db_connection()
                cursor = connection.cursor(dictionary=True)

                cursor.execute(
                    "UPDATE properties SET status = %s WHERE id = %s",
                    (
                        status,
                        property_id,
                    ),
                )
                connection.commit()
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = {"success": True, "message": "Made Rent Successfully"}
                self.wfile.write(json.dumps(response).encode("utf-8"))
        elif self.path.startswith("/api/makeavailable"):
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            property_id = data.get("property_id")
            token = self.headers.get("Authorization").split(" ")[1]
            verify = self.decode_token(token)
            if verify.get("error"):
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = {"success": False, "message": "token missing"}
                self.wfile.write(json.dumps(response).encode("utf-8"))
            else:
                status = "available"
                connection = get_db_connection()
                cursor = connection.cursor(dictionary=True)

                cursor.execute(
                    "UPDATE properties SET status = %s, booked_at = NULL, tenant_id=NULl WHERE id = %s",
                    (
                        status,
                        property_id,
                    ),
                )
                connection.commit()
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = {"success": True, "message": "Made Rent Successfully"}
                self.wfile.write(json.dumps(response).encode("utf-8"))

        elif self.path == "/api/checkbookstatus":
            content_length = int(self.headers["Content-Length"])
            data = json.loads(self.rfile.read(content_length))
            product_id = data
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            token = self.headers.get("Authorization").split(" ")[1]
            verify = self.decode_token(token)
            if verify.get("error"):
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = {"success": False, "text": "Book", "disabled": False}
                self.wfile.write(json.dumps(response).encode("utf-8"))
            else:
                user_id = verify.get("user_id")
                cursor.execute(
                    "Select id,tenant_id,status from properties where id = %s",
                    (product_id,),
                )
                result = cursor.fetchone()
                if result.get("tenant_id") == user_id:
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    response = {
                        "success": True,
                        "text": "Cancel Booking",
                        "disabled": False,
                    }
                    self.wfile.write(json.dumps(response).encode("utf-8"))
                elif result.get("status").lower() == "available":
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    response = {"success": True, "text": "Book", "disabled": False}
                    self.wfile.write(json.dumps(response).encode("utf-8"))
                elif result.get("status").lower() == "rented":
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    response = {"success": True, "text": "Rented", "disabled": True}
                    self.wfile.write(json.dumps(response).encode("utf-8"))
                elif not result.get("tenant_id") == user_id:
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    response = {"success": True, "text": "Booked", "disabled": True}
                    self.wfile.write(json.dumps(response).encode("utf-8"))
                else:
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    response = {"success": True, "text": "Book", "disabled": False}
                    self.wfile.write(json.dumps(response).encode("utf-8"))
        elif self.path == "/api/checksavedproduct":
            content_length = int(self.headers["Content-Length"])
            data = json.loads(self.rfile.read(content_length))
            product_id = data
            connection = get_db_connection()
            cursor = connection.cursor()
            token = self.headers.get("Authorization").split(" ")[1]
            verify = self.decode_token(token)
            if verify.get("error"):
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = {"success": False, "text": "Save"}
                self.wfile.write(json.dumps(response).encode("utf-8"))
            else:
                user_id = verify.get("user_id")
                cursor.execute(
                    "Select property_id from usersaved where property_id = %s and user_id = %s",
                    (product_id, user_id),
                )
                result = cursor.fetchone()
                if result:
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    response = {"success": True, "text": "Saved"}
                    self.wfile.write(json.dumps(response).encode("utf-8"))

                else:
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    response = {"success": True, "text": "Save"}
                    self.wfile.write(json.dumps(response).encode("utf-8"))

        elif self.path == "/api/bookproperty":
            content_length = int(self.headers["Content-Length"])
            data = json.loads(self.rfile.read(content_length))
            product_id = data
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            token = self.headers.get("Authorization").split(" ")[1]
            verify = self.decode_token(token)
            if verify.get("error"):
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = {
                    "message": "Not logged in",
                    "success": False,
                    "not_logged_in": True,
                }
                self.wfile.write(json.dumps(response).encode("utf-8"))
            else:
                userid = verify.get("user_id")
                cursor.execute(
                    "select id,status,tenant_id from properties where id = %s and tenant_id = %s",
                    (product_id, userid),
                )
                property = cursor.fetchone()
                if property:
                    status = "available"
                    cursor.execute(
                        "update properties set tenant_id = NULL,booked_at = NULL, status = %s where id = %s and tenant_id = %s",
                        (status, property["id"], userid),
                    )
                    connection.commit()
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    response = {
                        "message": "Booking process executed",
                        "success": True,
                        "text": "Book",
                    }
                    self.wfile.write(json.dumps(response).encode("utf-8"))
                else:
                    status = "booked"
                    booked_at = datetime.datetime.now()
                    cursor.execute(
                        "update properties set tenant_id = %s,booked_at = %s, status = %s where id = %s",
                        (userid, booked_at, status, product_id),
                    )
                    connection.commit()
                    cursor.execute(
                        """SELECT 
    owner.username AS owner_username, 
    owner.email AS owner_email, 
    tenant.username AS tenant_username,
    tenant.email AS tenant_email
FROM properties p
JOIN users owner ON owner.id = p.owner_id
LEFT JOIN users tenant ON tenant.id = p.tenant_id
WHERE p.id =%s;""",
                        (product_id,),
                    )
                    result = cursor.fetchone()
                    print(result.get("owner_email"))
                    send_email(
                        result.get("owner_email"),
                        f"Your Property has been Booked",
                        f"Your Property has been booked by {result.get("tenant_username")}. You can email him at {result.get("tenant_email")} for further negotiation.",
                    )
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    response = {
                        "message": "User registered successfully",
                        "success": True,
                        "text": "Cancel Booking",
                    }
                    self.wfile.write(json.dumps(response).encode("utf-8"))

        elif self.path == "/api/saveproduct":
            content_length = int(self.headers["Content-Length"])
            data = json.loads(self.rfile.read(content_length))
            product_id = data
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            token = self.headers.get("Authorization").split(" ")[1]
            verify = self.decode_token(token)
            print(f"this is token {verify}")
            if verify.get("error"):
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = {
                    "message": "Not logged in",
                    "success": False,
                }
                self.wfile.write(json.dumps(response).encode("utf-8"))
            else:
                user_id = verify.get("user_id")
                cursor.execute(
                    "Select property_id from usersaved where property_id = %s and user_id = %s",
                    (product_id, user_id),
                )
                result = cursor.fetchone()
                if result:
                    cursor.execute(
                        "Delete from usersaved where property_id = %s and user_id = %s",
                        (product_id, user_id),
                    )
                    connection.commit()
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    response = {
                        "message": "Product unsaved successfully",
                        "success": True,
                        "text": "Save",
                    }
                    self.wfile.write(json.dumps(response).encode("utf-8"))
                else:
                    cursor.execute(
                        "INSERT INTO usersaved (property_id, user_id) VALUES (%s, %s)",
                        (product_id, user_id),
                    )
                    connection.commit()
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    response = {
                        "message": "Product saved successfully",
                        "success": True,
                        "text": "Saved",
                    }
                    self.wfile.write(json.dumps(response).encode("utf-8"))
        elif self.path == "/api/postreview":
            content_length = int(self.headers["Content-Length"])
            data = json.loads(self.rfile.read(content_length))
            print("this is iddd")
            print(data)
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            token = self.headers.get("Authorization").split(" ")[1]
            verify = self.decode_token(token)
            if verify.get("error"):
                self.send_response(400)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                with open("static/loginpage/login.html", "r") as file:
                    html_content = file.read()
                self.wfile.write(html_content.encode("utf-8"))
            else:
                tenant_id = verify.get("user_id")
                rating = data.get("rating")
                review = data.get("review")
                property_id = data.get("property_id")

                cursor.execute(
                    "INSERT INTO reviews (tenant_id,property_id,rating,comment) VALUES (%s, %s, %s, %s)",
                    (tenant_id, property_id, rating, review),
                )
                connection.commit()
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = {
                    "message": "Review Posted",
                    "success": True,
                }
                self.wfile.write(json.dumps(response).encode("utf-8"))

        elif self.path == "/api/login":
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
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
                    print(result[0])
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

        elif self.path.startswith("/api/updateproperty"):
            ctype, pdict = cgi.parse_header(self.headers.get("content-type"))
            if ctype == "multipart/form-data":
                pdict["boundary"] = bytes(pdict["boundary"], "utf-8")
                fields = cgi.parse_multipart(self.rfile, pdict)
                raw_token = self.headers.get("Authorization")
                if not raw_token:
                    self._set_headers(404, "application/json")
                    response = {"message": "Token Missing", "success": False}
                    self.wfile.write(json.dumps(response).encode("utf-8"))
                # Decode token
                token = self.decode_token(raw_token.split(" ")[1])
                if token.get("error"):
                    self._set_headers(status_code=404, content_type="application/json")
                    response = {
                        "message": "Token missing. Please Relogin",
                        "success": False,
                    }
                    return self.wfile.write(json.dumps(response).encode("utf-8"))

                owner_id = token.get("user_id")
                title = fields.get("title")[0]
                property_id = int(self.path.split("/")[-1])
                description = fields.get("description")[0]
                house_number = fields.get("house_number")[0]
                street_name = fields.get("street_name")[0]
                country = fields.get("country")[0]
                city = fields.get("city")[0]
                state = fields.get("state")[0]
                zip_code = fields.get("zip_code")[0]
                price = float(fields.get("price")[0])
                status = (
                    fields.get("status")[0] if fields.get("status") else "available"
                )
                views = 0

                # Save images
                image_paths = {}
                upload_dir = "propertyimages/"
                os.makedirs(upload_dir, exist_ok=True)
                for field in ["thumbnail", "image1", "image2", "image3", "image4"]:
                    if fields.get(field):
                        file_item = fields[field][0]

                        # Manually set the extension if you know it
                        file_extension = ".jpg"  # Set a default extension; you can change it as needed

                        # Or use the content type if available
                        content_type = mimetypes.guess_extension(
                            file_item
                        )  # Assuming fields[field] has a content_type attribute
                        if content_type:
                            if "jpeg" in content_type:
                                file_extension = ".jpg"
                            elif "png" in content_type:
                                file_extension = ".png"
                            # Add other content types if needed

                        print(f"This is the image name: {field}")

                        file_path = os.path.join(
                            upload_dir,
                            f"{owner_id}_{self.generate_random_string(10)}{file_extension}",
                        )  # Include the extension
                        with open(file_path, "wb") as f:
                            f.write(file_item)  # Write the file content directly

                        image_paths[field] = file_path
                    else:
                        continue

                # Save to database
                self.edit_property_to_db(
                    property_id,
                    owner_id,
                    title,
                    description,
                    house_number,
                    street_name,
                    country,
                    city,
                    state,
                    zip_code,
                    price,
                    status,
                    views,
                    image_paths.get("thumbnail"),
                    image_paths.get("image1"),
                    image_paths.get("image2"),
                    image_paths.get("image3"),
                    image_paths.get("image4"),
                )

                self._set_headers(status_code=201, content_type="application/json")
                response = {"message": "Property added successfully", "success": True}
                self.wfile.write(json.dumps(response).encode("utf-8"))

        elif self.path == "/api/addproperty":
            ctype, pdict = cgi.parse_header(self.headers.get("content-type"))
            if ctype == "multipart/form-data":
                pdict["boundary"] = bytes(pdict["boundary"], "utf-8")
                fields = cgi.parse_multipart(self.rfile, pdict)
                raw_token = self.headers.get("Authorization")
                if not raw_token:
                    self._set_headers(404, "application/json")
                    response = {"message": "Token Missing", "success": False}
                    self.wfile.write(json.dumps(response).encode("utf-8"))
                # Decode token
                token = self.decode_token(raw_token.split(" ")[1])
                if token.get("error"):
                    self._set_headers(status_code=404, content_type="application/json")
                    response = {
                        "message": "Token missing. Please Relogin",
                        "success": False,
                    }
                    return self.wfile.write(json.dumps(response).encode("utf-8"))

                else:
                    owner_id = token.get("user_id")
                    title = fields.get("title")[0]
                    description = fields.get("description")[0]
                    house_number = fields.get("house_number")[0]
                    street_name = fields.get("street_name")[0]
                    country = fields.get("country")[0]
                    city = fields.get("city")[0]
                    state = fields.get("state")[0]
                    zip_code = fields.get("zip_code")[0]
                    price = float(fields.get("price")[0])
                    status = (
                        fields.get("status")[0] if fields.get("status") else "available"
                    )
                    views = 0

                    # Save images
                    image_paths = {}
                    upload_dir = "propertyimages/"
                    os.makedirs(upload_dir, exist_ok=True)
                    print(f"this is thumbnail{fields["thumbnail"]}")
                    for field in ["thumbnail", "image1", "image2", "image3", "image4"]:
                        if fields.get(field):
                            file_item = fields[field][0]

                            # Manually set the extension if you know it
                            file_extension = ".jpg"  # Set a default extension; you can change it as needed

                            # Or use the content type if available
                            content_type = mimetypes.guess_extension(
                                file_item
                            )  # Assuming fields[field] has a content_type attribute
                            if content_type:
                                if "jpeg" in content_type:
                                    file_extension = ".jpg"
                                elif "png" in content_type:
                                    file_extension = ".png"
                                # Add other content types if needed

                            print(f"This is the image name: {field}")

                            file_path = os.path.join(
                                upload_dir,
                                f"{owner_id}_{self.generate_random_string(10)}{file_extension}",
                            )  # Include the extension
                            with open(file_path, "wb") as f:
                                f.write(file_item)  # Write the file content directly

                            image_paths[field] = file_path

                    # Save to database
                    self.add_property_to_db(
                        owner_id,
                        title,
                        description,
                        house_number,
                        street_name,
                        country,
                        city,
                        state,
                        zip_code,
                        price,
                        status,
                        views,
                        image_paths.get("thumbnail"),
                        image_paths.get("image1"),
                        image_paths.get("image2"),
                        image_paths.get("image3"),
                        image_paths.get("image4"),
                    )

                    self._set_headers(status_code=201, content_type="application/json")
                    response = {
                        "message": "Property added successfully",
                        "success": True,
                    }
                    self.wfile.write(json.dumps(response).encode("utf-8"))

        else:
            self.send_response(404)
            response = {"message": "Not Found"}
            self.wfile.write(json.dumps(response).encode("utf-8"))

    def get_property_details(self, property_id):
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            sql_select_query = """SELECT 
    p.*,
    owner.username AS owner_name,
    owner.email AS owner_email,
    tenant.username AS tenant_name,
    tenant.email AS tenant_email
FROM 
    properties p
JOIN 
    users owner ON p.owner_id = owner.id
LEFT JOIN 
    users tenant ON p.tenant_id = tenant.id
WHERE 
    p.id = %s;
"""
            cursor.execute(sql_select_query, (property_id,))
            property_data = cursor.fetchone()
            # get_reviews = "SELECT * FROM reviews WHERE property_id = %s"
            get_reviews = """
    SELECT r.id AS review_id, r.rating, r.comment, r.created_at AS review_created_at,
           u.username, u.email, u.id 
    FROM reviews r
    JOIN users u ON r.tenant_id = u.id
    WHERE r.property_id = %s
    ORDER BY r.created_at DESC;
"""
            cursor.execute(get_reviews, (property_id,))
            property_reviews = cursor.fetchall()
            if property_data:
                sql_update_query = (
                    "UPDATE properties SET views = views + 1 WHERE id = %s"
                )
                cursor.execute(sql_update_query, (property_id,))
                connection.commit()
            cursor.close()
            connection.close()
            return property_data, property_reviews
        except Exception as e:
            print(f"Failed to retrieve property details from MySQL table: {e}")
            return None

    def getBookedStatus(self, property_id):
        try:
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            sql_select_query = "SELECT status,tenant_id FROM properties WHERE id = %s"
            cursor.execute(sql_select_query, (property_id,))
            property_data = cursor.fetchone()
            if property_data["status"] == "booked":
                html_string = f"""
                    <p class="font-bold cursor-pointer mx-2 hidden" id="bookbutton" data="{property_id}"
                                onclick="bookproduct()">Cancel Book</p>
                """
            else:
                html_string = f"""
                    <p class="font-bold cursor-pointer mx-2" id="bookbutton" data="{property_id}"
                                onclick="bookproduct()">Book</p>
                """
            return html_string
        except Exception as e:
            print(f"Failed to retrieve property details from MySQL table: {e}")
            return None

    def render_user_property_details(self, property_data, property_reviews):
        print(property_data)
        with open("static/details/userpropertydetail.html", "r") as file:
            html_template = file.read()
        html_content = html_template.replace("{{title}}", property_data["title"])
        html_content = html_content.replace(
            "{{description}}", property_data["description"]
        )
        html_content = html_content.replace("{{propertyid}}", str(property_data["id"]))
        html_content = html_content.replace(
            "{{house_number}}", str(property_data["house_number"])
        )
        html_content = html_content.replace(
            "{{street_name}}", property_data["street_name"]
        )
        html_content = html_content.replace("{{country}}", property_data["country"])
        html_content = html_content.replace("{{city}}", property_data["city"])
        html_content = html_content.replace("{{state}}", property_data["state"])
        html_content = html_content.replace("{{zip_code}}", property_data["zip_code"])
        html_content = html_content.replace("{{price}}", str(property_data["price"]))
        if (
            property_data["status"].lower() == "booked"
            or property_data["status"].lower() == "rented"
        ):
            html_content = html_content.replace(
                "{{status}}",
                f"{property_data["status"]} by {property_data["tenant_name"]}",
            )
        else:
            html_content = html_content.replace("{{status}}", property_data["status"])

        html_content = html_content.replace("{{views}}", str(property_data["views"]))
        images_html = ""
        image_urls = [property_data.get(f"image{i}", "") for i in range(1, 4)]
        for image_url in image_urls:
            if image_url:  # Only add non-empty images
                images_html += f'<img src="/{image_url}" alt="Property Image" class="rounded-md border-black" onclick="changeImage(\'{image_url}\')" style="width:200px;height:150px;">\n'
        image1html = ""
        image1html += f'<img src="/{image_urls[0]}" class="rounded-md border-black" alt="Property Image" id="mainImage" style="width:400px;height:300px;">'

        # Replace the images placeholder with the dynamically generated HTML
        html_content = html_content.replace("{{images}}", images_html)
        html_content = html_content.replace("{{firstimage}}", image1html)
        reviews = ""
        total_rates = 0
        total_ratings = 0
        for review in property_reviews:
            print(review)
            total_rates = total_rates + review.get("rating")
            total_ratings += 1
            star = ""
            numstars = 0
            for _ in range(review.get("rating")):
                star += "<span>&#9733;</span>"
                numstars += 1
            reviews += f"""
                    <div class="max-w-md w-full p-4 bg-white shadow-lg rounded-lg border border-gray-200">
                            <div class="flex space-x-2 justify-start" id="review_heading">
                                
                                <!-- Rating Stars -->
                                    <div class="flex text-yellow-500">
                                        {star}
                                    </div>
                                    <p class="text-sm text-gray-500">{numstars} out of 5 stars</p>
                            </div>

                            <!-- Review Description -->
                            <div class="mt-3 border p-2 rounded-lg border-gray-200">
                                <p class="text-gray-700 text-base">{review.get("comment")}</p>
                            </div>

                            <!-- Reviewer Info -->
                            <div class="mt-4 flex items-center space-x-3">
                                <div>
                                    <p class="text-sm font-semibold">{review.get("username")}</p>
                                    <p class="text-sm font-semibold">{review.get("email")}</p>
                                    <p class="text-xs text-gray-400">Reviewed on: {review.get("review_created_at")}</p>
                                </div>
                            </div>
                        </div>
                """
        html_content = html_content.replace("{{reviews_list}}", reviews)
        if total_ratings == 0:
            html_content = html_content.replace("{{average_rating}}", str(0))
        else:
            average_rating = round(total_rates / total_ratings, 2)
            html_content = html_content.replace(
                "{{average_rating}}", str(average_rating)
            )
        html_content = html_content.replace("{{no_of_ratings}}", str(total_ratings))
        return html_content

    def render_property_details(self, property_data, property_reviews):
        print(property_reviews)
        with open("static/details/propertydetails.html", "r") as file:
            html_template = file.read()
        html_content = html_template.replace("{{title}}", property_data["title"])
        html_content = html_content.replace(
            "{{description}}", property_data["description"]
        )
        html_content = html_content.replace("{{propertyid}}", str(property_data["id"]))
        html_content = html_content.replace(
            "{{house_number}}", str(property_data["house_number"])
        )
        html_content = html_content.replace(
            "{{street_name}}", property_data["street_name"]
        )
        html_content = html_content.replace("{{country}}", property_data["country"])
        html_content = html_content.replace("{{city}}", property_data["city"])
        html_content = html_content.replace("{{state}}", property_data["state"])
        html_content = html_content.replace("{{zip_code}}", property_data["zip_code"])
        html_content = html_content.replace("{{price}}", str(property_data["price"]))
        html_content = html_content.replace("{{status}}", property_data["status"])
        html_content = html_content.replace("{{views}}", str(property_data["views"]))
        images_html = ""
        image_urls = [property_data.get(f"image{i}", "") for i in range(1, 4)]
        for image_url in image_urls:
            if image_url:  # Only add non-empty images
                images_html += f'<img src="/{image_url}" alt="Property Image" class="rounded-md border-black" onclick="changeImage(\'{image_url}\')" style="width:200px;height:150px;">\n'
        image1html = ""
        image1html += f'<img src="/{image_urls[0]}" class="rounded-md border-black" alt="Property Image" id="mainImage" style="width:400px;height:300px;">'

        # Replace the images placeholder with the dynamically generated HTML
        html_content = html_content.replace("{{images}}", images_html)
        html_content = html_content.replace("{{firstimage}}", image1html)
        reviews = ""
        total_rates = 0
        total_ratings = 0
        for review in property_reviews:
            print(review)
            total_rates = total_rates + review.get("rating")
            total_ratings += 1
            star = ""
            numstars = 0
            for _ in range(review.get("rating")):
                star += "<span>&#9733;</span>"
                numstars += 1
            reviews += f"""
                    <div class="max-w-md w-full p-4 bg-white shadow-lg rounded-lg border border-gray-200">
                            <div class="flex space-x-2 justify-start" id="review_heading">
                                
                                <!-- Rating Stars -->
                                    <div class="flex text-yellow-500">
                                        {star}
                                    </div>
                                    <p class="text-sm text-gray-500">{numstars} out of 5 stars</p>
                            </div>

                            <!-- Review Description -->
                            <div class="mt-3 border p-2 rounded-lg border-gray-200">
                                <p class="text-gray-700 text-base">{review.get("comment")}</p>
                            </div>

                            <!-- Reviewer Info -->
                            <div class="mt-4 flex items-center space-x-3">
                                <div>
                                    <p class="text-sm font-semibold">{review.get("username")}</p>
                                    <p class="text-sm font-semibold">{review.get("email")}</p>
                                    <p class="text-xs text-gray-400">Reviewed on: {review.get("review_created_at")}</p>
                                </div>
                            </div>
                        </div>
                """
        html_content = html_content.replace("{{reviews_list}}", reviews)
        if total_ratings == 0:
            html_content = html_content.replace("{{average_rating}}", str(0))
        else:
            average_rating = round(total_rates / total_ratings, 2)
            html_content = html_content.replace(
                "{{average_rating}}", str(average_rating)
            )
        html_content = html_content.replace("{{no_of_ratings}}", str(total_ratings))
        return html_content

    def render_search_details(self, property_data):
        with open("static/dashboard/searchresult.html", "r") as file:
            html_template = file.read()
        cards = ""
        if len(property_data) > 0:
            for property in property_data:
                cards += f"""
                    <div class="bg-violet-50 hover:bg-violet-200 min-h-96 max-h-96 cursor-pointer hov flex flex-col p-4 m-1 shadow-md rounded-md">
                        <div class="flex justify-between">
                            <h2 class="text-xl">{property['title']}</h2>
                            <p class="font-mono text-sm capitalize">{property['status']}</p>
                        </div>
                        <div class="py-2 flex justify-center items-center">
                            <img src="../../{property['thumbnail']}" class="object-cover min-h-44 max-h-44 w-full">
                        </div>
                        <small class="text-[16px] text-left">Buy it at NPR. <script>document.write(formatCustomNumber({property['price']}));</script></small>
                        <small class="capitalize text-left">Located in {property['street_name']}, {property['city']}, {property['state']}</small>
                        <small class="text-left capitalize"><script>document.write(truncateString('{property.get('description', '')}', 100, true));</script></small>
                        <a href="/api/details/{property['id']}" class="pt-2 text-center text-[14px] hover:underline underline-offset-2 hover:text-blue-800"> View More</a>
                    </div>
                """
        else:
            cards += f"""
                <p class="flex justify-center">No results found</p>
"""

        html_content = html_template.replace("{{results}}", cards)
        return html_content

    def render_property_edit_details(self, property_data):
        with open("static/details/editproperty.html", "r") as file:
            html_template = file.read()
        html_content = html_template.replace("{{title}}", property_data["title"])
        html_content = html_content.replace(
            "{{description}}", property_data["description"]
        )
        html_content = html_content.replace("{{propertyid}}", str(property_data["id"]))
        html_content = html_content.replace(
            "{{house_number}}", str(property_data["house_number"])
        )
        html_content = html_content.replace(
            "{{street_name}}", property_data["street_name"]
        )
        html_content = html_content.replace("{{country}}", property_data["country"])
        html_content = html_content.replace("{{city}}", property_data["city"])
        html_content = html_content.replace("{{state}}", property_data["state"])
        html_content = html_content.replace("{{zip_code}}", property_data["zip_code"])
        html_content = html_content.replace("{{price}}", str(property_data["price"]))
        html_content = html_content.replace("{{status}}", property_data["status"])
        html_content = html_content.replace("{{views}}", str(property_data["views"]))

        # Replace the images placeholder with the dynamically generated HTML
        html_content = html_content.replace("{{image1}}", property_data.get("image1"))
        html_content = html_content.replace("{{image2}}", property_data.get("image2"))
        html_content = html_content.replace("{{image3}}", property_data.get("image3"))
        html_content = html_content.replace("{{image4}}", property_data.get("image4"))

        return html_content

    def getSaved(self, userid):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT property_id FROM usersaved WHERE user_id=%s", (userid,))
        propertyids = cursor.fetchall()
        print(propertyids)
        properties = []
        for property in propertyids:
            cursor.execute(
                "SELECT * FROM properties where id = %s", (property["property_id"],)
            )
            propertydetails = cursor.fetchone()
            for key, value in propertydetails.items():
                if isinstance(value, decimal.Decimal):
                    propertydetails[key] = float(value)
                if isinstance(value, datetime.datetime):
                    propertydetails[key] = value.strftime("%d/%m/%Y %H:%M:%S")
            properties.append(propertydetails)

        return {"properties": properties}

    def getAnalytics(self, userid):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM properties WHERE owner_id = {userid}")
        properties = cursor.fetchall()
        cursor.execute(f"SELECT * FROM properties WHERE tenant_id = {userid}")
        tenantmode = cursor.fetchall()
        views = 0
        available = 0
        rented = 0
        booked = 0
        userbooked = 0
        userrented = 0
        for property in properties:
            for key, value in property.items():
                if isinstance(value, decimal.Decimal):
                    property[key] = float(value)
                if key.lower() == "views":
                    views += value
                if key.lower() == "status" and value.lower() == "available":
                    available += 1
                if key.lower() == "status" and value.lower() == "booked":
                    booked += 1
                if key.lower() == "status" and value.lower() == "rented":
                    rented += 1.0
        for properties in tenantmode:
            for key, value in properties.items():
                if isinstance(value, decimal.Decimal):
                    properties[key] = float(value)
            if (
                properties.get("status").lower() == "booked"
                and properties.get("tenant_id") == userid
            ):
                userbooked += 1
            if (
                properties.get("status").lower() == "rented"
                and properties.get("tenant_id") == userid
            ):
                userrented += 1

        return {
            "views": views,
            "available": available,
            "booked": booked,
            "rented": rented,
            "user_id": userid,
            "user_booked": userbooked,
            "user_rented": userrented,
        }

    def get_trending_from_db(self, page=1, page_size=6):
        try:
            offset = (page - 1) * page_size
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            order_by = "-views"
            cursor.execute(
                f"SELECT id, title, description, price, status, thumbnail, house_number,street_name,country, city, state, zip_code FROM properties WHERE status = 'available' ORDER BY {order_by} LIMIT {page_size} OFFSET {offset}"
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

    def getAllUserProperties(self, userid):
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(f"SELECT * FROM properties WHERE owner_id = {userid}")
        properties = cursor.fetchall()

        for property in properties:
            for key, value in property.items():
                if isinstance(value, decimal.Decimal):
                    property[key] = float(value)
                if isinstance(value, datetime.datetime):
                    property[key] = value.strftime("%d/%m/%Y %H:%M:%S")

        return properties

    def get_recommended_from_db(self, page=1, page_size=6):
        try:
            offset = (page - 1) * page_size
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            order_by = "created_at"
            cursor.execute(
                f"SELECT id, title, description, price,status, house_number,street_name,country,thumbnail, city, state, zip_code FROM properties WHERE status = 'available' ORDER BY {order_by} LIMIT {page_size} OFFSET {offset}"
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
                f"SELECT id, title, description, price,status, house_number,street_name,country,thumbnail, city, state, zip_code FROM properties WHERE status = 'available' ORDER BY {order_by} LIMIT {page_size} OFFSET {offset}"
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
                "SELECT id, title, description, price, house_number,street_name,country,thumbnail, city, state, zip_code FROM properties WHERE status = 'available' LIMIT %s OFFSET %s",
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

    def add_property_to_db(
        self,
        owner_id,
        title,
        description,
        house_number,
        street_name,
        country,
        city,
        state,
        zip_code,
        price,
        status,
        views,
        thumbnail,
        image1,
        image2,
        image3,
        image4,
    ):
        try:
            # Establish database connection
            connection = get_db_connection()

            if connection.is_connected():
                cursor = connection.cursor()

                # Insert property details into the properties table
                insert_query = """
                INSERT INTO properties 
                (owner_id, title, description, house_number,street_name, city, state, zip_code,country, price, status,views, thumbnail, image1, image2, image3, image4) 
                VALUES (%s, %s, %s, %s, %s,%s,%s, %s, %s,%s, %s, %s, %s, %s, %s, %s, %s)
                """
                record = (
                    owner_id,
                    title,
                    description,
                    house_number,
                    street_name,
                    city,
                    state,
                    zip_code,
                    country,
                    price,
                    status,
                    views,
                    thumbnail,
                    image1,
                    image2,
                    image3,
                    image4,
                )
                cursor.execute(insert_query, record)
                connection.commit()

                print("Property inserted successfully into properties table")

        except Exception as e:
            print("Error while connecting to MySQL", str(e))
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
                print("MySQL connection is closed")

    def edit_property_to_db(
        self,
        property_id,
        owner_id,
        title,
        description,
        house_number,
        street_name,
        country,
        city,
        state,
        zip_code,
        price,
        status,
        views,
        thumbnail,
        image1,
        image2,
        image3,
        image4,
    ):
        try:
            # Establish database connection
            connection = get_db_connection()

            if connection.is_connected():
                cursor = connection.cursor()

                # Insert property details into the properties table
                insert_query = """
                UPDATE properties SET title = %s, description = %s, house_number = %s,street_name = %s, city = %s, state = %s, zip_code = %s,country = %s, price = %s, status = %s,views = %s, thumbnail = %s, image1 = %s, image2 = %s, image3 = %s, image4 = %s 
                WHERE id = %s AND owner_id = %s
                """
                record = (
                    title,
                    description,
                    house_number,
                    street_name,
                    city,
                    state,
                    zip_code,
                    country,
                    price,
                    status,
                    views,
                    thumbnail,
                    image1,
                    image2,
                    image3,
                    image4,
                    property_id,
                    owner_id,
                )
                cursor.execute(insert_query, record)
                connection.commit()

                print("Property inserted successfully into properties table")

        except Exception as e:
            print("Error while connecting to MySQL", str(e))
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()
                print("MySQL connection is closed")

    def generate_random_string(self, length=10):
        letters_and_digits = string.ascii_letters + string.digits
        random_string = "".join(
            random.choice(letters_and_digits) for i in range(length)
        )
        return random_string


# Usage example
# add_property_to_db(owner_id, title, description, address, city, state, zip_code, price, status, thumbnail, image1, image2, image3, image4)


def periodic_task():
    print(f"Periodic task is running... at {datetime.datetime.now()}")
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    status = "booked"
    cursor.execute("Select * FROM properties where status = %s", (status,))
    result = cursor.fetchall()
    today = datetime.datetime.today().date()
    print(today)
    for properties in result:
        if not properties.get("booked_at") == None:
            if (today - properties.get("booked_at").date()).days > 7:
                status = "available"
                cursor.execute(
                    """
                        SELECT 
    owner.username AS owner_username, 
    owner.email AS owner_email, 
    tenant.username AS tenant_username,
    tenant.email AS tenant_email
FROM properties p
JOIN users owner ON owner.id = p.owner_id
LEFT JOIN users tenant ON tenant.id = p.tenant_id
WHERE p.id = %s;

                    """,
                    (properties["id"],),
                )
                result = cursor.fetchone()

                cursor.execute(
                    "update properties set tenant_id = NULL,booked_at = NULL, status = %s where id = %s",
                    (status, properties["id"]),
                )
                send_email(
                    recipient_email=result.get("owner_email"),
                    subject=f"Property Status changed to Available",
                    body=f"Your Property status has been changed to available as it has been booked by {result.get("tenant_username")} for more than 7 days and no action has been performed on it.",
                )
                send_email(
                    recipient_email=result.get("tenant_email"),
                    subject="Your Booked Property has been cancelled",
                    body=f"The property you had booked has not been finalized. So in order to make it accessed by other users it has been cancelled and made available",
                )
                connection.commit()
                connection.close()
                connection.disconnect()

    Timer(43200, periodic_task).start()


def run():
    server_address = ("", 7000)
    httpd = HTTPServer(server_address, RequestHandler)
    print("Server is running at http://localhost:7000")
    # periodic_task()
    httpd.serve_forever()


if __name__ == "__main__":
    run()
