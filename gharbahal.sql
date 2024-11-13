USE gharbahal;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    number INT UNIQUE,
    password VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    role ENUM('tenant', 'owner') NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE properties (
    id INT AUTO_INCREMENT PRIMARY KEY,
    owner_id INT,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    house_number INT NOT NULL,
    street_name VARCHAR(255) NOT NULL,
    city VARCHAR(100) NOT NULL,
    state VARCHAR(100) NOT NULL,
    zip_code VARCHAR(20) NOT NULL,
    country VARCHAR(50) NOT NULL DEFAULT 'Nepal',
    price DECIMAL(10, 2) NOT NULL,
    status ENUM('available', 'booked', 'rented') DEFAULT 'available',
    type ENUM('house','flat','room') DEFAULT 'house',
    views INT,
    tenant_id INT,
    booked_at DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    thumbnail VARCHAR(255),
    image1 VARCHAR(255),
    image2 VARCHAR(255),
    image3 VARCHAR(255),
    image4 VARCHAR(255),
    FOREIGN KEY (owner_id) REFERENCES users(id),
    FOREIGN KEY (tenant_id) REFERENCES users(id)
);

CREATE TABLE usersaved(
    id INT AUTO_INCREMENT PRIMARY KEY,
    property_id INT,
    user_id INT,
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (property_id) REFERENCES properties(id)
);

CREATE TABLE reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tenant_id INT,
    property_id INT,
    rating INT CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tenant_id) REFERENCES users(id),
    FOREIGN KEY (property_id) REFERENCES properties(id)
);