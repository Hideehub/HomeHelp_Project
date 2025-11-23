-- MySQL dump 10.13  Distrib 9.5.0, for macos14.8 (x86_64)
--
-- Host: localhost    Database: homehelp_db
-- ------------------------------------------------------
-- Server version	9.5.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
SET @MYSQLDUMP_TEMP_LOG_BIN = @@SESSION.SQL_LOG_BIN;
SET @@SESSION.SQL_LOG_BIN= 0;

--
-- GTID state at the beginning of the backup 
--

SET @@GLOBAL.GTID_PURGED=/*!80000 '+'*/ 'd4510d2c-c72d-11f0-8bde-7d3bb2cadefa:1-71';

--
-- Table structure for table `admin`
--

DROP TABLE IF EXISTS `admin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `admin` (
  `admin_id` int NOT NULL AUTO_INCREMENT,
  `admin_username` varchar(100) NOT NULL,
  `admin_password` varchar(200) NOT NULL,
  `admin_email` varchar(255) NOT NULL,
  `admin_logindate` datetime DEFAULT NULL,
  PRIMARY KEY (`admin_id`),
  UNIQUE KEY `admin_email` (`admin_email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `admin`
--

LOCK TABLES `admin` WRITE;
/*!40000 ALTER TABLE `admin` DISABLE KEYS */;
/*!40000 ALTER TABLE `admin` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `alembic_version`
--

DROP TABLE IF EXISTS `alembic_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alembic_version`
--

LOCK TABLES `alembic_version` WRITE;
/*!40000 ALTER TABLE `alembic_version` DISABLE KEYS */;
INSERT INTO `alembic_version` VALUES ('928d2de4c420');
/*!40000 ALTER TABLE `alembic_version` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `category`
--

DROP TABLE IF EXISTS `category`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `category` (
  `cat_id` int NOT NULL AUTO_INCREMENT,
  `cat_name` varchar(100) NOT NULL,
  PRIMARY KEY (`cat_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `category`
--

LOCK TABLES `category` WRITE;
/*!40000 ALTER TABLE `category` DISABLE KEYS */;
/*!40000 ALTER TABLE `category` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `employer`
--

DROP TABLE IF EXISTS `employer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `employer` (
  `employer_id` int NOT NULL AUTO_INCREMENT,
  `employer_name` varchar(100) NOT NULL,
  `employer_email` varchar(255) NOT NULL,
  `employer_password` varchar(200) NOT NULL,
  `employer_address` text,
  `employer_gender` varchar(45) DEFAULT NULL,
  `employer_picture` varchar(100) DEFAULT NULL,
  `employer_phoneno` varchar(100) DEFAULT NULL,
  `date_registered` datetime DEFAULT NULL,
  `employer_stateid` int DEFAULT NULL,
  `employer_status` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`employer_id`),
  UNIQUE KEY `employer_email` (`employer_email`),
  KEY `employer_stateid` (`employer_stateid`),
  CONSTRAINT `employer_ibfk_1` FOREIGN KEY (`employer_stateid`) REFERENCES `state` (`state_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `employer`
--

LOCK TABLES `employer` WRITE;
/*!40000 ALTER TABLE `employer` DISABLE KEYS */;
/*!40000 ALTER TABLE `employer` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `experience`
--

DROP TABLE IF EXISTS `experience`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `experience` (
  `exp_id` int NOT NULL AUTO_INCREMENT,
  `exp_jobtitle` varchar(50) DEFAULT NULL,
  `exp_workerid` int DEFAULT NULL,
  `exp_about` text NOT NULL,
  `exp_years` varchar(50) NOT NULL,
  `exp_picture` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`exp_id`),
  KEY `exp_workerid` (`exp_workerid`),
  CONSTRAINT `experience_ibfk_1` FOREIGN KEY (`exp_workerid`) REFERENCES `worker` (`worker_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `experience`
--

LOCK TABLES `experience` WRITE;
/*!40000 ALTER TABLE `experience` DISABLE KEYS */;
/*!40000 ALTER TABLE `experience` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `jobapplication`
--

DROP TABLE IF EXISTS `jobapplication`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `jobapplication` (
  `app_id` int NOT NULL AUTO_INCREMENT,
  `app_status` enum('0','1') NOT NULL DEFAULT '0',
  `app_dateapplied` datetime DEFAULT NULL,
  `app_agreedamount` decimal(10,0) NOT NULL,
  `app_workerid` int DEFAULT NULL,
  PRIMARY KEY (`app_id`),
  KEY `app_workerid` (`app_workerid`),
  CONSTRAINT `jobapplication_ibfk_1` FOREIGN KEY (`app_workerid`) REFERENCES `worker` (`worker_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `jobapplication`
--

LOCK TABLES `jobapplication` WRITE;
/*!40000 ALTER TABLE `jobapplication` DISABLE KEYS */;
/*!40000 ALTER TABLE `jobapplication` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `jobposting`
--

DROP TABLE IF EXISTS `jobposting`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `jobposting` (
  `post_id` int NOT NULL AUTO_INCREMENT,
  `post_title` varchar(100) DEFAULT NULL,
  `post_description` text NOT NULL,
  `post_payrate` decimal(10,0) DEFAULT NULL,
  `post_dateadded` datetime DEFAULT NULL,
  `post_closingdate` datetime DEFAULT NULL,
  `post_status` enum('0','1') NOT NULL DEFAULT '0',
  `post_categoryid` int DEFAULT NULL,
  `post_employerid` int DEFAULT NULL,
  `post_workerid` int DEFAULT NULL,
  PRIMARY KEY (`post_id`),
  KEY `post_categoryid` (`post_categoryid`),
  KEY `post_employerid` (`post_employerid`),
  KEY `post_workerid` (`post_workerid`),
  CONSTRAINT `jobposting_ibfk_1` FOREIGN KEY (`post_categoryid`) REFERENCES `category` (`cat_id`),
  CONSTRAINT `jobposting_ibfk_2` FOREIGN KEY (`post_employerid`) REFERENCES `employer` (`employer_id`),
  CONSTRAINT `jobposting_ibfk_3` FOREIGN KEY (`post_workerid`) REFERENCES `worker` (`worker_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `jobposting`
--

LOCK TABLES `jobposting` WRITE;
/*!40000 ALTER TABLE `jobposting` DISABLE KEYS */;
/*!40000 ALTER TABLE `jobposting` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `payment`
--

DROP TABLE IF EXISTS `payment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `payment` (
  `pay_id` int NOT NULL AUTO_INCREMENT,
  `pay_amount` decimal(10,0) NOT NULL,
  `pay_date` datetime DEFAULT NULL,
  `pay_employerid` int DEFAULT NULL,
  `pay_workerid` int DEFAULT NULL,
  `pay_ref` varchar(100) DEFAULT NULL,
  `pay_status` enum('pending','paid','failed') NOT NULL DEFAULT 'pending',
  `pay_data` text,
  PRIMARY KEY (`pay_id`),
  KEY `pay_employerid` (`pay_employerid`),
  KEY `pay_workerid` (`pay_workerid`),
  CONSTRAINT `payment_ibfk_2` FOREIGN KEY (`pay_employerid`) REFERENCES `employer` (`employer_id`),
  CONSTRAINT `payment_ibfk_3` FOREIGN KEY (`pay_workerid`) REFERENCES `worker` (`worker_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `payment`
--

LOCK TABLES `payment` WRITE;
/*!40000 ALTER TABLE `payment` DISABLE KEYS */;
/*!40000 ALTER TABLE `payment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `review`
--

DROP TABLE IF EXISTS `review`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `review` (
  `review_id` int NOT NULL AUTO_INCREMENT,
  `review_rating` float DEFAULT NULL,
  `review_comment` text NOT NULL,
  `review_workerid` int DEFAULT NULL,
  `review_employerid` int DEFAULT NULL,
  PRIMARY KEY (`review_id`),
  KEY `review_employerid` (`review_employerid`),
  KEY `review_workerid` (`review_workerid`),
  CONSTRAINT `review_ibfk_1` FOREIGN KEY (`review_employerid`) REFERENCES `employer` (`employer_id`),
  CONSTRAINT `review_ibfk_2` FOREIGN KEY (`review_workerid`) REFERENCES `worker` (`worker_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `review`
--

LOCK TABLES `review` WRITE;
/*!40000 ALTER TABLE `review` DISABLE KEYS */;
/*!40000 ALTER TABLE `review` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `state`
--

DROP TABLE IF EXISTS `state`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `state` (
  `state_id` int NOT NULL AUTO_INCREMENT,
  `state_name` varchar(100) NOT NULL,
  PRIMARY KEY (`state_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `state`
--

LOCK TABLES `state` WRITE;
/*!40000 ALTER TABLE `state` DISABLE KEYS */;
/*!40000 ALTER TABLE `state` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `worker`
--

DROP TABLE IF EXISTS `worker`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `worker` (
  `worker_id` int NOT NULL AUTO_INCREMENT,
  `worker_fname` varchar(100) NOT NULL,
  `worker_lname` varchar(100) NOT NULL,
  `worker_email` varchar(255) NOT NULL,
  `worker_phoneno` varchar(100) NOT NULL,
  `worker_password` varchar(200) NOT NULL,
  `worker_status` varchar(10) DEFAULT '0',
  `worker_registrationdate` datetime DEFAULT NULL,
  `worker_gender` varchar(45) DEFAULT NULL,
  `worker_picture` varchar(100) DEFAULT NULL,
  `worker_availability` enum('0','1') NOT NULL DEFAULT '0',
  `worker_verification` enum('0','1') NOT NULL DEFAULT '0',
  `worker_address` text,
  `worker_stateid` int DEFAULT NULL,
  `worker_categoryid` int DEFAULT NULL,
  `worker_price` decimal(10,2) NOT NULL,
  PRIMARY KEY (`worker_id`),
  UNIQUE KEY `worker_email` (`worker_email`),
  KEY `worker_stateid` (`worker_stateid`),
  KEY `worker_categoryid` (`worker_categoryid`),
  CONSTRAINT `worker_ibfk_1` FOREIGN KEY (`worker_stateid`) REFERENCES `state` (`state_id`),
  CONSTRAINT `worker_ibfk_2` FOREIGN KEY (`worker_categoryid`) REFERENCES `category` (`cat_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `worker`
--

LOCK TABLES `worker` WRITE;
/*!40000 ALTER TABLE `worker` DISABLE KEYS */;
/*!40000 ALTER TABLE `worker` ENABLE KEYS */;
UNLOCK TABLES;
SET @@SESSION.SQL_LOG_BIN = @MYSQLDUMP_TEMP_LOG_BIN;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-11-22  0:27:08
