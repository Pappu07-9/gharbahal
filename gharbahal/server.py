from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import mysql.connector
from urllib.parse import urlparse, parse_qs
from hashlib import sha256

# Database configuration
db_config = {
    'user': 'root',
    'password': 'root',
    'host': 'localhost',
    'port':3306,
    'database': 'gharbahal'
}

# Establish database connection
def get_db_connection():
    return mysql.connector.connect(**db_config)

class RequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code=200, content_type='text/plain'):
        self.send_response(status_code)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', 'http://localhost:5500')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers()

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)

        self._set_headers(content_type='application/json')

        if self.path == '/register':
            email = data.get('email')
            password = data.get('password')
            if email and password:
                hashed_password = sha256(password.encode('utf-8')).hexdigest()

                connection = get_db_connection()
                cursor = connection.cursor()

                try:
                    cursor.execute('INSERT INTO users (email, password) VALUES (%s, %s)', (email, hashed_password))
                    connection.commit()
                    response = {'message': 'User registered successfully'}
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                except mysql.connector.Error as err:
                    response = {'error': str(err)}
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                finally:
                    cursor.close()
                    connection.close()

        elif self.path == '/login':
            email = data.get('email')
            password = data.get('password')
            if email and password:
                hashed_password = sha256(password.encode('utf-8')).hexdigest()

                connection = get_db_connection()
                cursor = connection.cursor()

                try:
                    cursor.execute('SELECT password FROM users WHERE email = %s', (email,))
                    result = cursor.fetchone()
                    if result and result[0] == hashed_password:
                        response = {'message': 'Login successful'}
                        self.wfile.write(json.dumps(response).encode('utf-8'))
                    else:
                        self.send_response(401)
                        response = {'message': 'Invalid email or password'}
                        self.wfile.write(json.dumps(response).encode('utf-8'))
                except mysql.connector.Error as err:
                    self.send_response(500)
                    response = {'error': str(err)}
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                finally:
                    cursor.close()
                    connection.close()

            else:
                self.send_response(400)
                response = {'message': 'Email and password are required'}
                self.wfile.write(json.dumps(response).encode('utf-8'))

        else:
            self.send_response(404)
            response = {'message': 'Not Found'}
            self.wfile.write(json.dumps(response).encode('utf-8'))

def run():
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, RequestHandler)
    print('Server is running at http://localhost:8000')
    httpd.serve_forever()

if __name__ == '__main__':
    run()
