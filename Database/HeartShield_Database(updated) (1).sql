-- MySQL dump 10.13  Distrib 8.0.46, for Win64 (x86_64)
--
-- Host: localhost    Database: heartshield_db
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `activity_logs`
--

DROP TABLE IF EXISTS `activity_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `activity_logs` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint unsigned DEFAULT NULL,
  `action` varchar(255) NOT NULL,
  `entity_type` varchar(100) DEFAULT NULL,
  `entity_id` bigint unsigned DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_activity_user` (`user_id`),
  KEY `idx_activity_created` (`created_at`),
  CONSTRAINT `fk_activity_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `activity_logs`
--

LOCK TABLES `activity_logs` WRITE;
/*!40000 ALTER TABLE `activity_logs` DISABLE KEYS */;
/*!40000 ALTER TABLE `activity_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `admins`
--

DROP TABLE IF EXISTS `admins`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `admins` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint unsigned NOT NULL,
  `admin_level` enum('super_admin','admin') DEFAULT 'admin',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `fk_admin_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `admins`
--

LOCK TABLES `admins` WRITE;
/*!40000 ALTER TABLE `admins` DISABLE KEYS */;
INSERT INTO `admins` VALUES (1,1,'super_admin','2026-09-14 17:27:07');
/*!40000 ALTER TABLE `admins` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `assessments`
--

DROP TABLE IF EXISTS `assessments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `assessments` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `patient_id` bigint unsigned NOT NULL,
  `systolic_bp` decimal(6,2) DEFAULT NULL,
  `diastolic_bp` decimal(6,2) DEFAULT NULL,
  `heart_rate` decimal(6,2) DEFAULT NULL,
  `total_cholesterol` decimal(7,2) DEFAULT NULL,
  `hdl` decimal(7,2) DEFAULT NULL,
  `ldl` decimal(7,2) DEFAULT NULL,
  `blood_glucose` decimal(7,2) DEFAULT NULL,
  `bmi` decimal(6,2) DEFAULT NULL,
  `diabetes` tinyint(1) DEFAULT '0',
  `hypertension` tinyint(1) DEFAULT '0',
  `previous_heart_disease` tinyint(1) DEFAULT '0',
  `family_history` tinyint(1) DEFAULT '0',
  `smoking` varchar(50) DEFAULT NULL,
  `alcohol` varchar(50) DEFAULT NULL,
  `physical_activity` varchar(50) DEFAULT NULL,
  `exercise_frequency` varchar(100) DEFAULT NULL,
  `diet` varchar(100) DEFAULT NULL,
  `sleep_duration` varchar(50) DEFAULT NULL,
  `sleep_quality` varchar(50) DEFAULT NULL,
  `stress_level` varchar(50) DEFAULT NULL,
  `sedentary_time` varchar(50) DEFAULT NULL,
  `assessment_status` enum('pending','completed','reviewed') DEFAULT 'completed',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_assessment_patient` (`patient_id`),
  KEY `idx_assessment_created` (`created_at`),
  CONSTRAINT `fk_assessment_patient` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `assessments`
--

LOCK TABLES `assessments` WRITE;
/*!40000 ALTER TABLE `assessments` DISABLE KEYS */;
INSERT INTO `assessments` VALUES (1,1,120.00,80.00,72.00,180.00,50.00,100.00,95.00,22.50,0,0,0,0,'Never','Never','Active','4-5 days/week','Balanced','7-8 hours','Good','Low','2-4 hours','completed','2026-09-16 07:31:21','2026-09-16 07:31:21'),(2,1,120.00,80.00,72.00,180.00,50.00,100.00,95.00,25.00,0,0,0,0,'Never','Never','Moderate','3–4 days/week','Balanced','7–8 hours','Good','Moderate','4–6 hours/day','completed','2026-09-16 07:55:25','2026-09-16 07:55:25'),(3,3,120.00,80.00,72.00,190.00,50.00,110.00,95.00,22.50,0,1,0,0,'Regularly','Regularly','Low','Never','Poor','Less than 5 hours','Poor','Very High','More than 8 hours/day','completed','2026-09-17 04:26:40','2026-09-17 04:26:40');
/*!40000 ALTER TABLE `assessments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `doctor_assessment_reviews`
--

DROP TABLE IF EXISTS `doctor_assessment_reviews`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `doctor_assessment_reviews` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `assessment_id` bigint unsigned NOT NULL,
  `doctor_id` bigint unsigned NOT NULL,
  `patient_id` bigint unsigned NOT NULL,
  `review_notes` text,
  `doctor_recommendations` text,
  `review_status` enum('pending','reviewed') DEFAULT 'reviewed',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_review_assessment` (`assessment_id`),
  KEY `idx_review_doctor` (`doctor_id`),
  KEY `idx_review_patient` (`patient_id`),
  CONSTRAINT `fk_review_assessment` FOREIGN KEY (`assessment_id`) REFERENCES `assessments` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_review_doctor` FOREIGN KEY (`doctor_id`) REFERENCES `doctors` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_review_patient` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `doctor_assessment_reviews`
--

LOCK TABLES `doctor_assessment_reviews` WRITE;
/*!40000 ALTER TABLE `doctor_assessment_reviews` DISABLE KEYS */;
/*!40000 ALTER TABLE `doctor_assessment_reviews` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `doctor_notes`
--

DROP TABLE IF EXISTS `doctor_notes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `doctor_notes` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `doctor_id` bigint unsigned NOT NULL,
  `patient_id` bigint unsigned NOT NULL,
  `note` text NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_doctor_notes_doctor` (`doctor_id`),
  KEY `idx_doctor_notes_patient` (`patient_id`),
  CONSTRAINT `fk_doctor_notes_doctor` FOREIGN KEY (`doctor_id`) REFERENCES `doctors` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_doctor_notes_patient` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `doctor_notes`
--

LOCK TABLES `doctor_notes` WRITE;
/*!40000 ALTER TABLE `doctor_notes` DISABLE KEYS */;
/*!40000 ALTER TABLE `doctor_notes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `doctor_patient_relationships`
--

DROP TABLE IF EXISTS `doctor_patient_relationships`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `doctor_patient_relationships` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `doctor_id` bigint unsigned NOT NULL,
  `patient_id` bigint unsigned NOT NULL,
  `relationship_status` enum('requested','active','inactive','rejected') DEFAULT 'requested',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_doctor_patient` (`doctor_id`,`patient_id`),
  KEY `fk_relationship_patient` (`patient_id`),
  CONSTRAINT `fk_relationship_doctor` FOREIGN KEY (`doctor_id`) REFERENCES `doctors` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_relationship_patient` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `doctor_patient_relationships`
--

LOCK TABLES `doctor_patient_relationships` WRITE;
/*!40000 ALTER TABLE `doctor_patient_relationships` DISABLE KEYS */;
/*!40000 ALTER TABLE `doctor_patient_relationships` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `doctors`
--

DROP TABLE IF EXISTS `doctors`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `doctors` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint unsigned NOT NULL,
  `specialization` varchar(150) DEFAULT NULL,
  `medical_license_number` varchar(100) DEFAULT NULL,
  `years_of_experience` int DEFAULT '0',
  `hospital_name` varchar(150) DEFAULT NULL,
  `hospital_address` text,
  `consultation_fee` decimal(10,2) DEFAULT NULL,
  `verification_status` enum('pending','verified','rejected') DEFAULT 'pending',
  `bio` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  UNIQUE KEY `medical_license_number` (`medical_license_number`),
  CONSTRAINT `fk_doctor_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `doctors`
--

LOCK TABLES `doctors` WRITE;
/*!40000 ALTER TABLE `doctors` DISABLE KEYS */;
INSERT INTO `doctors` VALUES (1,5,'Cardiology','MH123456',5,'HeartShield Medical Center',NULL,NULL,'pending',NULL,'2026-09-23 12:13:07','2026-09-23 12:13:07'),(2,6,'Cardiologist','HM126H',7,'ITM Hospital',NULL,NULL,'pending',NULL,'2026-09-23 12:54:01','2026-09-23 12:54:01'),(3,9,'Cardiology','TEST-LICENSE-001',5,'HeartShield Test Hospital',NULL,NULL,'pending',NULL,'2026-10-03 17:33:04','2026-10-03 17:33:04'),(4,8,'Cardiology','HM125H',5,'ITM Hospital',NULL,NULL,'verified',NULL,'2026-10-04 17:22:15','2026-10-04 17:22:30'),(5,12,'Cardiology','HS-TEST-2026-001',5,'HeartShield Test Hospital',NULL,NULL,'rejected',NULL,'2026-10-04 17:27:34','2026-10-04 17:48:44'),(6,13,'Cardiology','HS-TEST-2026-002',5,'HeartShield Test Hospital',NULL,NULL,'verified',NULL,'2026-10-04 17:29:52','2026-10-04 17:43:02'),(7,14,'Cardiology','HS-TEST-2026-003',5,'HeartShield Test Hospital',NULL,NULL,'verified',NULL,'2026-10-04 19:48:55','2026-10-04 20:13:03');
/*!40000 ALTER TABLE `doctors` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `feedback`
--

DROP TABLE IF EXISTS `feedback`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `feedback` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint unsigned NOT NULL,
  `rating` tinyint unsigned NOT NULL,
  `feedback_text` text NOT NULL,
  `category` varchar(50) DEFAULT 'other',
  `status` enum('new','reviewed','resolved') DEFAULT 'new',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_feedback_user` (`user_id`),
  KEY `idx_feedback_status` (`status`),
  CONSTRAINT `fk_feedback_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `chk_feedback_rating` CHECK ((`rating` between 1 and 5))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `feedback`
--

LOCK TABLES `feedback` WRITE;
/*!40000 ALTER TABLE `feedback` DISABLE KEYS */;
INSERT INTO `feedback` VALUES (1,1,5,'HeartShield prediction system is easy to use.','general','reviewed','2026-10-04 21:09:12','2026-10-04 21:17:06');
/*!40000 ALTER TABLE `feedback` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `model_predictions`
--

DROP TABLE IF EXISTS `model_predictions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `model_predictions` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `assessment_id` bigint unsigned NOT NULL,
  `logistic_probability` decimal(6,5) DEFAULT NULL,
  `random_forest_probability` decimal(6,5) DEFAULT NULL,
  `xgboost_probability` decimal(6,5) DEFAULT NULL,
  `ensemble_probability` decimal(6,5) NOT NULL,
  `risk_level` enum('low','moderate','high') NOT NULL,
  `prediction_label` enum('low_risk','at_risk','high_risk') NOT NULL,
  `model_version` varchar(50) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_assessment_prediction` (`assessment_id`),
  CONSTRAINT `fk_prediction_assessment` FOREIGN KEY (`assessment_id`) REFERENCES `assessments` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `model_predictions`
--

LOCK TABLES `model_predictions` WRITE;
/*!40000 ALTER TABLE `model_predictions` DISABLE KEYS */;
/*!40000 ALTER TABLE `model_predictions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `notifications`
--

DROP TABLE IF EXISTS `notifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `notifications` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint unsigned NOT NULL,
  `title` varchar(200) NOT NULL,
  `message` text NOT NULL,
  `notification_type` enum('assessment','review','doctor','system','admin') NOT NULL,
  `is_read` tinyint(1) DEFAULT '0',
  `reference_type` varchar(100) DEFAULT NULL,
  `reference_id` bigint unsigned DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_notification_user` (`user_id`),
  KEY `idx_notification_read` (`is_read`),
  CONSTRAINT `fk_notification_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `notifications`
--

LOCK TABLES `notifications` WRITE;
/*!40000 ALTER TABLE `notifications` DISABLE KEYS */;
/*!40000 ALTER TABLE `notifications` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `otp_verifications`
--

DROP TABLE IF EXISTS `otp_verifications`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `otp_verifications` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint unsigned DEFAULT NULL,
  `email` varchar(255) NOT NULL,
  `otp_hash` varchar(255) NOT NULL,
  `purpose` varchar(50) NOT NULL DEFAULT 'verification',
  `expires_at` datetime NOT NULL,
  `is_used` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_otp_user_id` (`user_id`),
  KEY `idx_otp_email` (`email`),
  CONSTRAINT `fk_otp_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `otp_verifications`
--

LOCK TABLES `otp_verifications` WRITE;
/*!40000 ALTER TABLE `otp_verifications` DISABLE KEYS */;
INSERT INTO `otp_verifications` VALUES (1,7,'kishan260123@gmail.com','$2b$12$LDjIIiKMQotXWHPuFStxWODY4KqQKIT8PCWQYeTh9GzdTICa3xZoK','verification','2026-10-03 18:08:42',1,'2026-10-03 18:03:42'),(2,7,'Kishan260123@gmail.com','$2b$12$cFVrlofuXFQq5Esl1UqzXurO1fdDqciXgklO3SQbkdcOIgTDzb1Ry','verification','2026-10-03 18:11:44',1,'2026-10-03 18:06:44'),(3,11,'Kishan260123@gmail.com','$2b$12$FWQHxhGNWJIvCGrDRtp51O59sbwp1gjf2DbhPTJOzcbZh00l7TLYS','verification','2026-10-03 18:23:17',1,'2026-10-03 18:18:17'),(4,11,'Kishan260123@gmail.com','$2b$12$YU0a.Sv9kraY7H0winGy1u19e27TMVuyDOinpYA4abVoP1qpxvcRi','password_reset','2026-10-03 18:32:35',1,'2026-10-03 18:27:35'),(5,11,'Kishan260123@gmail.com','$2b$12$rqga0thADcoyK77op.GrHuRWeLH9ndP5aVzcoJdI3s0vDqBEbn6P2','password_reset','2026-10-03 18:35:19',1,'2026-10-03 18:30:19');
/*!40000 ALTER TABLE `otp_verifications` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `password_reset_tokens`
--

DROP TABLE IF EXISTS `password_reset_tokens`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `password_reset_tokens` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint unsigned NOT NULL,
  `token` varchar(255) NOT NULL,
  `expires_at` datetime NOT NULL,
  `is_used` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `token` (`token`),
  KEY `fk_reset_user` (`user_id`),
  CONSTRAINT `fk_reset_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `password_reset_tokens`
--

LOCK TABLES `password_reset_tokens` WRITE;
/*!40000 ALTER TABLE `password_reset_tokens` DISABLE KEYS */;
/*!40000 ALTER TABLE `password_reset_tokens` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `patient_health_information`
--

DROP TABLE IF EXISTS `patient_health_information`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `patient_health_information` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `patient_id` bigint unsigned NOT NULL,
  `height_cm` decimal(6,2) DEFAULT NULL,
  `weight_kg` decimal(6,2) DEFAULT NULL,
  `blood_group` varchar(10) DEFAULT NULL,
  `allergies` text,
  `current_medications` text,
  `medical_conditions` text,
  `previous_surgeries` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `systolic_bp` decimal(6,2) DEFAULT NULL,
  `diastolic_bp` decimal(6,2) DEFAULT NULL,
  `heart_rate` decimal(6,2) DEFAULT NULL,
  `total_cholesterol` decimal(7,2) DEFAULT NULL,
  `hdl` decimal(7,2) DEFAULT NULL,
  `ldl` decimal(7,2) DEFAULT NULL,
  `blood_glucose` decimal(7,2) DEFAULT NULL,
  `bmi` decimal(6,2) DEFAULT NULL,
  `diabetes` tinyint(1) DEFAULT '0',
  `hypertension` tinyint(1) DEFAULT '0',
  `previous_heart_disease` tinyint(1) DEFAULT '0',
  `family_history` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `patient_id` (`patient_id`),
  CONSTRAINT `fk_health_patient` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `patient_health_information`
--

LOCK TABLES `patient_health_information` WRITE;
/*!40000 ALTER TABLE `patient_health_information` DISABLE KEYS */;
INSERT INTO `patient_health_information` VALUES (1,1,NULL,NULL,NULL,NULL,'Aspirin','None',NULL,'2026-09-16 09:00:49','2026-09-16 15:40:12',17.00,NULL,24.00,NULL,8.00,NULL,NULL,NULL,0,0,0,1);
/*!40000 ALTER TABLE `patient_health_information` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `patient_lifestyle`
--

DROP TABLE IF EXISTS `patient_lifestyle`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `patient_lifestyle` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `patient_id` bigint unsigned NOT NULL,
  `smoking_status` enum('never','former','current') DEFAULT 'never',
  `alcohol_consumption` enum('never','occasional','moderate','heavy') DEFAULT 'never',
  `physical_activity_level` enum('low','moderate','high') DEFAULT 'moderate',
  `exercise_frequency` int DEFAULT NULL,
  `diet_type` varchar(100) DEFAULT NULL,
  `sleep_duration` decimal(4,2) DEFAULT NULL,
  `sleep_quality` enum('poor','average','good','excellent') DEFAULT NULL,
  `stress_level` enum('low','moderate','high') DEFAULT NULL,
  `sedentary_hours` decimal(4,2) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `patient_id` (`patient_id`),
  CONSTRAINT `fk_lifestyle_patient` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `patient_lifestyle`
--

LOCK TABLES `patient_lifestyle` WRITE;
/*!40000 ALTER TABLE `patient_lifestyle` DISABLE KEYS */;
INSERT INTO `patient_lifestyle` VALUES (1,1,'never','occasional','moderate',4,'Healthy',7.50,'good','moderate',5.00,'2026-09-16 14:14:48','2026-09-16 15:38:28'),(2,3,'current','moderate','low',0,'Healthy',6.50,'good','high',7.00,'2026-09-17 04:26:41','2026-09-23 11:48:17'),(3,4,'never','never','high',7,'Healthy',5.50,'poor','low',7.00,'2026-09-25 18:11:23','2026-09-25 18:11:23');
/*!40000 ALTER TABLE `patient_lifestyle` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `patients`
--

DROP TABLE IF EXISTS `patients`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `patients` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint unsigned NOT NULL,
  `date_of_birth` date DEFAULT NULL,
  `gender` enum('male','female','other') DEFAULT NULL,
  `blood_group` varchar(10) DEFAULT NULL,
  `emergency_contact_name` varchar(100) DEFAULT NULL,
  `emergency_contact_phone` varchar(20) DEFAULT NULL,
  `address` text,
  `city` varchar(100) DEFAULT NULL,
  `state` varchar(100) DEFAULT NULL,
  `country` varchar(100) DEFAULT 'India',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `assigned_doctor_id` bigint unsigned DEFAULT NULL,
  `emergency_contact_relationship` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  KEY `ix_patients_assigned_doctor_id` (`assigned_doctor_id`),
  CONSTRAINT `fk_patient_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_patients_assigned_doctor` FOREIGN KEY (`assigned_doctor_id`) REFERENCES `doctors` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `patients`
--

LOCK TABLES `patients` WRITE;
/*!40000 ALTER TABLE `patients` DISABLE KEYS */;
INSERT INTO `patients` VALUES (1,2,'2005-10-04','male','O+','Rohit Singh','8888888888','Gwalior, Madhya Pradesh','Gwalior','Madhya Pradesh','India','2026-09-15 06:40:21','2026-09-28 06:44:02',2,'brother'),(2,3,'2000-02-12','male',NULL,NULL,NULL,NULL,NULL,NULL,'India','2026-09-15 06:55:46','2026-10-04 18:06:06',6,'brother'),(3,4,'2000-10-10','male',NULL,'Nakul Jain','8454385734875','Thatipur, Gwalior\nKila Road Ambah',NULL,NULL,'India','2026-09-17 04:19:04','2026-09-28 06:44:02',NULL,'friend'),(4,7,'2006-08-12','male',NULL,'Yogendra Jain','7845987564','Thatpur',NULL,NULL,'India','2026-09-25 17:16:11','2026-09-28 06:04:17',NULL,'Brother'),(5,8,'2002-05-15','male',NULL,NULL,NULL,NULL,NULL,NULL,'India','2026-10-03 17:31:59','2026-10-03 17:31:59',NULL,NULL),(6,10,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'India','2026-10-03 17:52:45','2026-10-03 17:52:45',NULL,NULL),(7,11,'2006-01-23','male',NULL,NULL,NULL,NULL,NULL,NULL,'India','2026-10-03 18:15:41','2026-10-03 18:15:41',NULL,NULL);
/*!40000 ALTER TABLE `patients` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `recommendations`
--

DROP TABLE IF EXISTS `recommendations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `recommendations` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `assessment_id` bigint unsigned NOT NULL,
  `patient_id` bigint unsigned NOT NULL,
  `ai_summary` text,
  `risk_factors` json DEFAULT NULL,
  `improvement_areas` json DEFAULT NULL,
  `lifestyle_recommendations` json DEFAULT NULL,
  `diet_recommendations` json DEFAULT NULL,
  `exercise_recommendations` json DEFAULT NULL,
  `sleep_recommendations` json DEFAULT NULL,
  `stress_recommendations` json DEFAULT NULL,
  `doctor_consultation_advice` text,
  `llm_model` varchar(100) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `fk_recommendation_assessment` (`assessment_id`),
  KEY `idx_recommendation_patient` (`patient_id`),
  CONSTRAINT `fk_recommendation_assessment` FOREIGN KEY (`assessment_id`) REFERENCES `assessments` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_recommendation_patient` FOREIGN KEY (`patient_id`) REFERENCES `patients` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `recommendations`
--

LOCK TABLES `recommendations` WRITE;
/*!40000 ALTER TABLE `recommendations` DISABLE KEYS */;
/*!40000 ALTER TABLE `recommendations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_settings`
--

DROP TABLE IF EXISTS `user_settings`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_settings` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `user_id` bigint unsigned NOT NULL,
  `email_notifications` tinyint(1) DEFAULT '1',
  `assessment_notifications` tinyint(1) DEFAULT '1',
  `doctor_notifications` tinyint(1) DEFAULT '1',
  `system_notifications` tinyint(1) DEFAULT '1',
  `profile_visibility` tinyint(1) DEFAULT '1',
  `data_sharing` tinyint(1) DEFAULT '0',
  `language` varchar(20) DEFAULT 'en',
  `theme` varchar(20) DEFAULT 'light',
  `timezone` varchar(50) DEFAULT 'Asia/Kolkata',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_user_settings_user` (`user_id`),
  CONSTRAINT `fk_user_settings_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_settings`
--

LOCK TABLES `user_settings` WRITE;
/*!40000 ALTER TABLE `user_settings` DISABLE KEYS */;
INSERT INTO `user_settings` VALUES (1,1,0,1,0,1,0,1,'en','dark','Asia/Kolkata','2026-10-04 21:26:53','2026-10-04 21:34:38');
/*!40000 ALTER TABLE `user_settings` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` bigint unsigned NOT NULL AUTO_INCREMENT,
  `full_name` varchar(100) NOT NULL,
  `email` varchar(150) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` enum('patient','doctor','admin') NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `profile_image` varchar(255) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `is_verified` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'kishan sharma','admin@heartshield.com','$2b$12$p.Ela9x7F9OPnkdhukzrd.Ci.X5kShzJ5wTDBTfMGsKgMjU6Kmg9a','admin','7788956874',NULL,1,0,'2026-09-14 17:26:49','2026-10-04 21:29:23'),(2,'Kishan','testpatient01@gmail.com','$2b$12$fvoj9V3X65RTUwJgnLT7XupdTbmtkczguuA4stLLWAU2lzqK9Bhzm','patient','9752925111',NULL,1,0,'2026-09-15 06:40:21','2026-10-04 22:24:24'),(3,'Yogendra Jain','yogendra123@gmail.com','$2b$12$miGvHkdzdNiEQTWKF/lt8egeuEMpgykrEn5jYY2Swkt8UlNkbU.6S','patient','9696923230',NULL,1,0,'2026-09-15 06:55:46','2026-09-15 06:55:46'),(4,'Shaurya singh','test13@gmail.com','$2b$12$mFa3/7hOXDHL1BcQOh9jF.S9iGpOJqVrtE4bbuxdjtZXj92NeA1Ji','patient','7637637264',NULL,1,0,'2026-09-17 04:19:04','2026-09-17 04:20:21'),(5,'Dr. Rahul Sharma','doctor@heartshield.com','$2b$12$H4fSbumwfTmnbUA5boyz5OkTm3IyGDm5AhdZdCO94E2v4/tdu90WW','doctor','9876543210',NULL,1,1,'2026-09-23 12:13:07','2026-10-04 17:17:23'),(6,'Dr.Pramod Sharma','pramod@heartshield.co','$2b$12$B89.2GDey1wKyQ1fZLSfvuR1wPKmWGwSajJNfnQJrrdhWc5OFLr6C','doctor','9090012110',NULL,1,1,'2026-09-23 12:54:01','2026-10-04 17:17:23'),(7,'Kishan_Sharma','ks@gmal.com','$2b$12$CbFuaIThl2D2RKfA3xRBHupjEWraIpA5ozz48/VQoBWEGoZxfrEE6','patient','+917067800714',NULL,1,1,'2026-09-25 17:16:11','2026-10-03 18:15:35'),(8,'Test Patient','testpatient01@example.com','$2b$12$SiVlHbfRJ7AJvqotZsrlRebTDZna/XyNPUvNWWq69M1MnfPYKIPYW','patient','9876543210',NULL,1,0,'2026-10-03 17:31:59','2026-10-03 17:31:59'),(9,'Test Doctor','testdoctor01@example.com','$2b$12$/WhX6wJLuEXSWxmpWVNSrOdoGqhSxFuNbO9pGU6eI4RBZ8aC7VJ76','doctor','9876543211',NULL,1,1,'2026-10-03 17:33:04','2026-10-04 17:17:23'),(10,'General Test Patient','generalpatient01@example.com','$2b$12$Jxwub1oknpsd6X/GmoelrOjkd1dl32XmWKsNQHprb7kYHwFxcb0t.','patient','9876543212',NULL,1,0,'2026-10-03 17:52:45','2026-10-03 17:52:45'),(11,'Kishan Sharma','kishan260123@gmail.com','$2b$12$WVhrXpQxEm6tnWBFp26lQO5ywPP.BJbQVnzRLV5JSFBOQ50fVydA2','patient','7067800714',NULL,1,1,'2026-10-03 18:15:41','2026-10-03 18:32:03'),(12,'HeartShield Test Doctor','your_doctor_email@example.com','$2b$12$8CNFBfQNKjM4SvPcRsnOquyH7fVdD1HyrPlXkktXpNc9JVx41LsH2','doctor','9876543210',NULL,1,0,'2026-10-04 17:27:34','2026-10-04 17:27:34'),(13,'HeartShield Test Doctor','kishan@gmail.com','$2b$12$jtGS6ROE9YM./MIQ3BQYreM71oAAF0.hD8E/Jdg/kgKj6kHlR87Ra','doctor','9876543211',NULL,1,0,'2026-10-04 17:29:52','2026-10-04 17:29:52'),(14,'HeartShield Test Doctor','ki@12gmail.com','$2b$12$oE9NiXPmH0FjSN74djT7Vu96xIZISAEflZE6V2.6LwNphWcudswji','doctor','9876543211',NULL,1,0,'2026-10-04 19:48:55','2026-10-04 20:11:07');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-10 23:45:45
