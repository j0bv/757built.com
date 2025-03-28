-- Run this if you haven't created the tables yet
CREATE TABLE technology_areas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE consolidated_developments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    technology_area_id INT,
    key_players TEXT,
    technological_development TEXT,
    project_cost TEXT,
    information_date DATE,
    event_location TEXT, 
    contact_information TEXT,
    number_of_sources INT,
    consolidation_date TIMESTAMP,
    FOREIGN KEY (technology_area_id) REFERENCES technology_areas(id)
);
