-- Flight Booking System Database Schema

-- Airlines table
CREATE TABLE IF NOT EXISTS Airlines (
    airline_id INTEGER PRIMARY KEY AUTOINCREMENT,
    airline_code TEXT NOT NULL UNIQUE,
    airline_name TEXT NOT NULL,
    country TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Airports table
CREATE TABLE IF NOT EXISTS Airports (
    airport_id INTEGER PRIMARY KEY AUTOINCREMENT,
    airport_code TEXT NOT NULL UNIQUE,
    airport_name TEXT NOT NULL,
    city TEXT NOT NULL,
    country TEXT NOT NULL,
    timezone TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Flights table
CREATE TABLE IF NOT EXISTS Flights (
    flight_id INTEGER PRIMARY KEY AUTOINCREMENT,
    airline_id INTEGER NOT NULL,
    flight_number TEXT NOT NULL,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    departure_time TIMESTAMP NOT NULL,
    arrival_time TIMESTAMP NOT NULL,
    base_price REAL NOT NULL,
    total_seats INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(airline_id) REFERENCES Airlines(airline_id),
    FOREIGN KEY(origin) REFERENCES Airports(airport_code),
    FOREIGN KEY(destination) REFERENCES Airports(airport_code)
);

-- Seats table
CREATE TABLE IF NOT EXISTS Seats (
    seat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    flight_id INTEGER NOT NULL,
    seat_class TEXT NOT NULL,
    initial_inventory INTEGER NOT NULL,
    available_seats INTEGER NOT NULL,
    price_multiplier REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(flight_id) REFERENCES Flights(flight_id) ON DELETE CASCADE,
    UNIQUE(flight_id, seat_class)
);

-- Users table
CREATE TABLE IF NOT EXISTS Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bookings table
CREATE TABLE IF NOT EXISTS Bookings (
    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    flight_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    seat_class TEXT NOT NULL,
    seats_booked INTEGER NOT NULL,
    final_price REAL NOT NULL,
    booking_date TIMESTAMP NOT NULL,
    status TEXT NOT NULL,
    pnr TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(flight_id) REFERENCES Flights(flight_id),
    FOREIGN KEY(user_id) REFERENCES Users(user_id)
);

-- Passengers table
CREATE TABLE IF NOT EXISTS Passengers (
    passenger_id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    passport_number TEXT,
    date_of_birth TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(booking_id) REFERENCES Bookings(booking_id) ON DELETE CASCADE
);

-- Transactions table
CREATE TABLE IF NOT EXISTS Transactions (
    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    payment_method TEXT NOT NULL,
    status TEXT NOT NULL,
    transaction_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(booking_id) REFERENCES Bookings(booking_id)
);

-- BookingHistory table for audit trail
CREATE TABLE IF NOT EXISTS BookingHistory (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    booking_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    details TEXT,
    performed_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(booking_id) REFERENCES Bookings(booking_id) ON DELETE CASCADE
);

-- FareHistory table for price tracking
CREATE TABLE IF NOT EXISTS FareHistory (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    flight_id INTEGER NOT NULL,
    base_price REAL NOT NULL,
    dynamic_price REAL NOT NULL,
    seat_class TEXT NOT NULL,
    occupancy_ratio REAL NOT NULL,
    demand_level TEXT NOT NULL,
    recorded_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(flight_id) REFERENCES Flights(flight_id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_flights_origin_dest_date ON Flights(origin, destination, date(departure_time));
CREATE INDEX IF NOT EXISTS idx_bookings_user ON Bookings(user_id);
CREATE INDEX IF NOT EXISTS idx_bookings_flight ON Bookings(flight_id);
CREATE INDEX IF NOT EXISTS idx_farehistory_flight ON FareHistory(flight_id, recorded_at);

-- Insert sample data for Airlines
INSERT INTO Airlines (airline_code, airline_name, country) VALUES
('UA', 'United Airlines', 'USA'),
('AA', 'American Airlines', 'USA'),
('DL', 'Delta Air Lines', 'USA'),
('LH', 'Lufthansa', 'Germany'),
('BA', 'British Airways', 'United Kingdom'),
('EK', 'Emirates', 'United Arab Emirates'),
('SQ', 'Singapore Airlines', 'Singapore'),
('QR', 'Qatar Airways', 'Qatar');

-- Insert sample data for Airports
INSERT INTO Airports (airport_code, airport_name, city, country, timezone) VALUES
('JFK', 'John F. Kennedy International Airport', 'New York', 'USA', 'America/New_York'),
('LAX', 'Los Angeles International Airport', 'Los Angeles', 'USA', 'America/Los_Angeles'),
('ORD', 'O''Hare International Airport', 'Chicago', 'USA', 'America/Chicago'),
('LHR', 'Heathrow Airport', 'London', 'United Kingdom', 'Europe/London'),
('CDG', 'Charles de Gaulle Airport', 'Paris', 'France', 'Europe/Paris'),
('FRA', 'Frankfurt Airport', 'Frankfurt', 'Germany', 'Europe/Berlin'),
('DXB', 'Dubai International Airport', 'Dubai', 'United Arab Emirates', 'Asia/Dubai'),
('SIN', 'Singapore Changi Airport', 'Singapore', 'Singapore', 'Asia/Singapore'),
('HND', 'Haneda Airport', 'Tokyo', 'Japan', 'Asia/Tokyo'),
('SYD', 'Sydney Airport', 'Sydney', 'Australia', 'Australia/Sydney'),
('DOH', 'Hamad International Airport', 'Doha', 'Qatar', 'Asia/Qatar');

-- Insert sample Users
INSERT INTO Users (username, email, first_name, last_name) VALUES
('user1', 'user1@example.com', 'John', 'Doe'),
('user2', 'user2@example.com', 'Jane', 'Smith'),
('user3', 'user3@example.com', 'Robert', 'Johnson');

-- Insert sample Flights (using date 30 days from now)
INSERT INTO Flights (airline_id, flight_number, origin, destination, departure_time, arrival_time, base_price, total_seats) VALUES
(1, 'UA101', 'JFK', 'LAX', datetime('now', '+30 days', '+8 hours'), datetime('now', '+30 days', '+11 hours', '+30 minutes'), 300.00, 180),
(2, 'AA202', 'LAX', 'JFK', datetime('now', '+30 days', '+10 hours'), datetime('now', '+30 days', '+18 hours', '+30 minutes'), 320.00, 200),
(3, 'DL303', 'ORD', 'LHR', datetime('now', '+31 days', '+9 hours'), datetime('now', '+31 days', '+22 hours', '+45 minutes'), 650.00, 220),
(4, 'LH404', 'FRA', 'JFK', datetime('now', '+32 days', '+11 hours'), datetime('now', '+32 days', '+23 hours'), 700.00, 250),
(5, 'BA505', 'LHR', 'SIN', datetime('now', '+33 days', '+13 hours'), datetime('now', '+34 days', '+7 hours'), 850.00, 280),
(6, 'EK606', 'DXB', 'SYD', datetime('now', '+34 days', '+2 hours'), datetime('now', '+34 days', '+14 hours', '+30 minutes'), 950.00, 300),
(7, 'SQ707', 'SIN', 'HND', datetime('now', '+35 days', '+7 hours'), datetime('now', '+35 days', '+13 hours'), 400.00, 220),
(8, 'QR808', 'DOH', 'CDG', datetime('now', '+36 days', '+8 hours'), datetime('now', '+36 days', '+14 hours'), 600.00, 260),
(1, 'UA111', 'JFK', 'LHR', datetime('now', '+25 days', '+16 hours'), datetime('now', '+26 days', '+5 hours'), 680.00, 220),
(2, 'AA212', 'LAX', 'SYD', datetime('now', '+26 days', '+10 hours'), datetime('now', '+27 days', '+22 hours'), 920.00, 250),
(3, 'DL333', 'ORD', 'CDG', datetime('now', '+27 days', '+9 hours'), datetime('now', '+27 days', '+18 hours', '+40 minutes'), 540.00, 200),
(4, 'LH422', 'FRA', 'DXB', datetime('now', '+28 days', '+7 hours'), datetime('now', '+28 days', '+15 hours'), 480.00, 210),
(5, 'BA515', 'LHR', 'JFK', datetime('now', '+29 days', '+12 hours'), datetime('now', '+29 days', '+20 hours'), 610.00, 230),
(6, 'EK618', 'DXB', 'SIN', datetime('now', '+30 days', '+4 hours'), datetime('now', '+30 days', '+12 hours'), 510.00, 260),
(7, 'SQ719', 'SIN', 'SYD', datetime('now', '+31 days', '+6 hours'), datetime('now', '+31 days', '+14 hours'), 530.00, 240),
(8, 'QR828', 'CDG', 'HND', datetime('now', '+32 days', '+9 hours'), datetime('now', '+33 days', '+1 hours', '+15 minutes'), 780.00, 210),
(1, 'UA131', 'JFK', 'ORD', datetime('now', '+33 days', '+5 hours'), datetime('now', '+33 days', '+8 hours'), 280.00, 190),
(2, 'AA242', 'ORD', 'LAX', datetime('now', '+34 days', '+6 hours'), datetime('now', '+34 days', '+9 hours'), 260.00, 180);

-- Insert sample Seats for each flight
-- Flight 1: UA101
INSERT INTO Seats (flight_id, seat_class, initial_inventory, available_seats, price_multiplier) VALUES
(1, 'Economy', 150, 150, 1.0),
(1, 'Business', 30, 30, 2.2);

-- Flight 2: AA202
INSERT INTO Seats (flight_id, seat_class, initial_inventory, available_seats, price_multiplier) VALUES
(2, 'Economy', 160, 160, 1.0),
(2, 'Business', 40, 40, 2.3);

-- Flight 3: DL303
INSERT INTO Seats (flight_id, seat_class, initial_inventory, available_seats, price_multiplier) VALUES
(3, 'Economy', 180, 180, 1.0),
(3, 'Business', 40, 40, 2.2);

-- Flight 4: LH404
INSERT INTO Seats (flight_id, seat_class, initial_inventory, available_seats, price_multiplier) VALUES
(4, 'Economy', 200, 200, 1.0),
(4, 'Business', 50, 50, 2.5);

-- Flight 5: BA505
INSERT INTO Seats (flight_id, seat_class, initial_inventory, available_seats, price_multiplier) VALUES
(5, 'Economy', 220, 220, 1.0),
(5, 'Business', 60, 60, 2.4);

-- Flight 6: EK606
INSERT INTO Seats (flight_id, seat_class, initial_inventory, available_seats, price_multiplier) VALUES
(6, 'Economy', 240, 240, 1.0),
(6, 'Business', 60, 60, 2.3);

-- Flight 7: SQ707
INSERT INTO Seats (flight_id, seat_class, initial_inventory, available_seats, price_multiplier) VALUES
(7, 'Economy', 180, 180, 1.0),
(7, 'Business', 40, 40, 2.2);

-- Flight 8: QR808
INSERT INTO Seats (flight_id, seat_class, initial_inventory, available_seats, price_multiplier) VALUES
(8, 'Economy', 200, 200, 1.0),
(8, 'Business', 60, 60, 2.5);

-- Flight 9: UA111
INSERT INTO Seats (flight_id, seat_class, initial_inventory, available_seats, price_multiplier) VALUES
(9, 'Economy', 170, 170, 1.0),
(9, 'Business', 50, 50, 2.3);

-- Flight 10: AA212
INSERT INTO Seats (flight_id, seat_class, initial_inventory, available_seats, price_multiplier) VALUES
(10, 'Economy', 210, 210, 1.0),
(10, 'Business', 40, 40, 2.4);

-- Flight 11: DL333
INSERT INTO Seats (flight_id, seat_class, initial_inventory, available_seats, price_multiplier) VALUES
(11, 'Economy', 160, 160, 1.0),
(11, 'Business', 40, 40, 2.2);

-- Flight 12: LH422
INSERT INTO Seats (flight_id, seat_class, initial_inventory, available_seats, price_multiplier) VALUES
(12, 'Economy', 180, 180, 1.0),
(12, 'Business', 30, 30, 2.1);

-- Flight 13: BA515
INSERT INTO Seats (flight_id, seat_class, initial_inventory, available_seats, price_multiplier) VALUES
(13, 'Economy', 190, 190, 1.0),
(13, 'Business', 40, 40, 2.3);

-- Flight 14: EK618
INSERT INTO Seats (flight_id, seat_class, initial_inventory, available_seats, price_multiplier) VALUES
(14, 'Economy', 220, 220, 1.0),
(14, 'Business', 40, 40, 2.4);

-- Flight 15: SQ719
INSERT INTO Seats (flight_id, seat_class, initial_inventory, available_seats, price_multiplier) VALUES
(15, 'Economy', 200, 200, 1.0),
(15, 'Business', 40, 40, 2.2);

-- Flight 16: QR828
INSERT INTO Seats (flight_id, seat_class, initial_inventory, available_seats, price_multiplier) VALUES
(16, 'Economy', 180, 180, 1.0),
(16, 'Business', 30, 30, 2.4);

-- Flight 17: UA131
INSERT INTO Seats (flight_id, seat_class, initial_inventory, available_seats, price_multiplier) VALUES
(17, 'Economy', 160, 160, 1.0),
(17, 'Business', 30, 30, 2.2);

-- Flight 18: AA242
INSERT INTO Seats (flight_id, seat_class, initial_inventory, available_seats, price_multiplier) VALUES
(18, 'Economy', 150, 150, 1.0),
(18, 'Business', 30, 30, 2.1);