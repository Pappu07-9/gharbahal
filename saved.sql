USE gharbahal;

CREATE TABLE usersaved(
    id INT AUTO_INCREMENT PRIMARY KEY,
    property_id INT,
    user_id INT,
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (property_id) REFERENCES properties(id)
);