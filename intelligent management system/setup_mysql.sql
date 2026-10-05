-- ==========================================================
-- WORKFORCE INTELLIGENCE & MANAGEMENT PLATFORM
-- MySQL Database Schema Creation Script
-- ==========================================================

CREATE DATABASE IF NOT EXISTS `workforce_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `workforce_db`;

-- Disable foreign key checks for clean recreation
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `notifications`;
DROP TABLE IF EXISTS `leave_requests`;
DROP TABLE IF EXISTS `attendance`;
DROP TABLE IF EXISTS `task_reassignments`;
DROP TABLE IF EXISTS `tasks`;
DROP TABLE IF EXISTS `employee_skills`;
DROP TABLE IF EXISTS `skills`;
DROP TABLE IF EXISTS `employees`;
DROP TABLE IF EXISTS `teams`;
DROP TABLE IF EXISTS `departments`;
DROP TABLE IF EXISTS `users`;
DROP TABLE IF EXISTS `roles`;

SET FOREIGN_KEY_CHECKS = 1;

-- 1. ROLES TABLE
CREATE TABLE `roles` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(50) NOT NULL UNIQUE,
    `description` VARCHAR(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. USERS TABLE
CREATE TABLE `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(100) NOT NULL UNIQUE,
    `email` VARCHAR(150) NOT NULL UNIQUE,
    `password_hash` VARCHAR(255) NOT NULL,
    `role_id` INT NOT NULL,
    `is_active` BOOLEAN DEFAULT TRUE,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_users_role` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. DEPARTMENTS TABLE
CREATE TABLE `departments` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL UNIQUE,
    `code` VARCHAR(20) NOT NULL UNIQUE,
    `description` TEXT,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. TEAMS TABLE
CREATE TABLE `teams` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL,
    `department_id` INT NOT NULL,
    `manager_id` INT NULL,
    `team_lead_id` INT NULL,
    `capacity` INT DEFAULT 100,
    `status` VARCHAR(20) DEFAULT 'Active',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_teams_dept` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. EMPLOYEES TABLE
CREATE TABLE `employees` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL UNIQUE,
    `emp_code` VARCHAR(20) NOT NULL UNIQUE,
    `full_name` VARCHAR(150) NOT NULL,
    `phone` VARCHAR(30),
    `designation` VARCHAR(100),
    `department_id` INT NULL,
    `team_id` INT NULL,
    `manager_id` INT NULL,
    `team_lead_id` INT NULL,
    `joining_date` DATE NOT NULL,
    `status` VARCHAR(20) DEFAULT 'Active',
    `avatar` VARCHAR(255) DEFAULT 'default_avatar.png',
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_emp_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_emp_dept` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_emp_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_emp_manager` FOREIGN KEY (`manager_id`) REFERENCES `employees` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_emp_lead` FOREIGN KEY (`team_lead_id`) REFERENCES `employees` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Add foreign keys to teams for manager and team_lead
ALTER TABLE `teams`
    ADD CONSTRAINT `fk_team_manager` FOREIGN KEY (`manager_id`) REFERENCES `employees` (`id`) ON DELETE SET NULL,
    ADD CONSTRAINT `fk_team_lead` FOREIGN KEY (`team_lead_id`) REFERENCES `employees` (`id`) ON DELETE SET NULL;

-- 6. SKILLS TABLE
CREATE TABLE `skills` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL UNIQUE,
    `category` VARCHAR(50) DEFAULT 'Technical',
    `description` VARCHAR(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. EMPLOYEE_SKILLS TABLE
CREATE TABLE `employee_skills` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `employee_id` INT NOT NULL,
    `skill_id` INT NOT NULL,
    `proficiency` VARCHAR(30) DEFAULT 'Intermediate', -- Beginner, Intermediate, Advanced, Expert
    CONSTRAINT `fk_es_emp` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_es_skill` FOREIGN KEY (`skill_id`) REFERENCES `skills` (`id`) ON DELETE CASCADE,
    CONSTRAINT `uq_emp_skill` UNIQUE (`employee_id`, `skill_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 8. TASKS TABLE
CREATE TABLE `tasks` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `task_code` VARCHAR(30) NOT NULL UNIQUE,
    `title` VARCHAR(200) NOT NULL,
    `description` TEXT,
    `required_skill_id` INT NULL,
    `priority` VARCHAR(20) DEFAULT 'Medium', -- Low, Medium, High, Critical
    `status` VARCHAR(30) DEFAULT 'Assigned', -- Not Started, Assigned, In Progress, Blocked, Completed, Delayed
    `progress` INT DEFAULT 0, -- 0 to 100
    `assigned_to` INT NULL,
    `team_id` INT NULL,
    `created_by` INT NOT NULL,
    `start_date` DATE NOT NULL,
    `due_date` DATE NOT NULL,
    `completed_at` DATETIME NULL,
    `remarks` TEXT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_task_skill` FOREIGN KEY (`required_skill_id`) REFERENCES `skills` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_task_assigned` FOREIGN KEY (`assigned_to`) REFERENCES `employees` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_task_team` FOREIGN KEY (`team_id`) REFERENCES `teams` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_task_creator` FOREIGN KEY (`created_by`) REFERENCES `employees` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. TASK REASSIGNMENTS AUDIT TABLE
CREATE TABLE `task_reassignments` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `task_id` INT NOT NULL,
    `previous_employee_id` INT NULL,
    `new_employee_id` INT NOT NULL,
    `reassigned_by` INT NOT NULL,
    `reason` VARCHAR(255),
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_tr_task` FOREIGN KEY (`task_id`) REFERENCES `tasks` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_tr_prev` FOREIGN KEY (`previous_employee_id`) REFERENCES `employees` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_tr_new` FOREIGN KEY (`new_employee_id`) REFERENCES `employees` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_tr_by` FOREIGN KEY (`reassigned_by`) REFERENCES `employees` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 10. ATTENDANCE TABLE
CREATE TABLE `attendance` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `employee_id` INT NOT NULL,
    `date` DATE NOT NULL,
    `check_in` TIME NULL,
    `check_out` TIME NULL,
    `working_hours` DECIMAL(4, 2) DEFAULT 0.00,
    `status` VARCHAR(20) DEFAULT 'Present', -- Present, Late, Half Day, Absent
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_att_emp` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`) ON DELETE CASCADE,
    CONSTRAINT `uq_emp_date` UNIQUE (`employee_id`, `date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 11. LEAVE REQUESTS TABLE
CREATE TABLE `leave_requests` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `employee_id` INT NOT NULL,
    `leave_type` VARCHAR(50) NOT NULL, -- Casual Leave, Sick Leave, Earned Leave, Maternity/Paternity
    `start_date` DATE NOT NULL,
    `end_date` DATE NOT NULL,
    `days_count` INT NOT NULL DEFAULT 1,
    `reason` TEXT NOT NULL,
    `status` VARCHAR(20) DEFAULT 'Pending', -- Pending, Approved, Rejected
    `reviewed_by` INT NULL,
    `rejection_reason` TEXT NULL,
    `impact_warning` TEXT NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_leave_emp` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_leave_reviewer` FOREIGN KEY (`reviewed_by`) REFERENCES `employees` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 12. NOTIFICATIONS TABLE
CREATE TABLE `notifications` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `title` VARCHAR(150) NOT NULL,
    `message` TEXT NOT NULL,
    `type` VARCHAR(20) DEFAULT 'info', -- info, success, warning, danger
    `link` VARCHAR(255) NULL,
    `is_read` BOOLEAN DEFAULT FALSE,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_notif_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
