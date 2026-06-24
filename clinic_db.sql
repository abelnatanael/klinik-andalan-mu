CREATE DATABASE IF NOT EXISTS clinic_reservation;
USE clinic_reservation;

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

-- =========================
-- 1. TABLE USERS
-- =========================
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'user') NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- 2. TABLE DOCTORS
-- =========================
CREATE TABLE doctors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    doctor_name VARCHAR(100) NOT NULL,
    specialization VARCHAR(100) NOT NULL,
    schedule_day VARCHAR(50) NOT NULL,
    schedule_time VARCHAR(50) NOT NULL,
    photo VARCHAR(255) DEFAULT 'default-doctor.jpg',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- 3. TABLE APPOINTMENTS
-- =========================
CREATE TABLE appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    complaint TEXT NOT NULL,
    status ENUM('pending', 'approved', 'rejected', 'completed') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_appointments_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_appointments_doctor
        FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- =========================
-- 4. TABLE AMBULANCE BOOKINGS
-- =========================
CREATE TABLE ambulance_bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    pickup_address TEXT NOT NULL,
    destination_address TEXT NOT NULL,
    booking_date DATE NOT NULL,
    booking_time TIME NOT NULL,
    notes TEXT,
    status ENUM('pending', 'processed', 'picked_up', 'cancelled') DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ambulance_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- =========================
-- DATA DUMMY DOCTORS
-- =========================
INSERT INTO doctors (doctor_name, specialization, schedule_day, schedule_time, photo) VALUES
('Dr. Abel Natanael', 'Umum', 'Senin - Jumat', '08:00 - 12:00', 'doctor1.jpg'),
('Dr. Siti Rahma', 'Anak', 'Senin - Kamis', '13:00 - 17:00', 'doctor2.jpg'),
('Dr. Ahmad Indra', 'Penyakit Dalam', 'Selasa - Sabtu', '09:00 - 14:00', 'doctor3.jpg');

COMMIT;