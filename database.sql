-- MySQL dump 10.17  Distrib 10.3.17-MariaDB, for debian-linux-gnueabihf (armv7l)
--
-- Host: localhost    Database: mediaController
-- ------------------------------------------------------
-- Server version	10.3.17-MariaDB-0+deb10u1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `episodes`
--

DROP TABLE IF EXISTS `episodes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `episodes` (
  `idEpisode` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `overview` text COLLATE utf8_unicode_ci DEFAULT NULL,
  `icon` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `season` int(11) DEFAULT NULL,
  `episode` int(11) DEFAULT NULL,
  `rating` int(11) DEFAULT NULL,
  `scraperName` char(10) COLLATE utf8_unicode_ci NOT NULL,
  `scraperID` int(11) NOT NULL,
  `path` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `idShow` int(11) DEFAULT NULL,
  `forceUpdate` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`idEpisode`),
  KEY `idShow` (`idShow`),
  CONSTRAINT `episodes_ibfk_1` FOREIGN KEY (`idShow`) REFERENCES `tv_shows` (`idShow`)
) ENGINE=InnoDB AUTO_INCREMENT=1346 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `scrapers`
--

DROP TABLE IF EXISTS `scrapers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `scrapers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `scraperName` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `scraperURL` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `scrapers`
--

LOCK TABLES `scrapers` WRITE;
/*!40000 ALTER TABLE `scrapers` DISABLE KEYS */;
INSERT INTO `scrapers` VALUES (1,'tmdb','https://www.themoviedb.org/tv/'),(2,'tvdb','https://thetvdb.com/?tab=series&id='),(3,'imdb','https://www.imdb.com/title/');
/*!40000 ALTER TABLE `scrapers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tv_shows`
--

DROP TABLE IF EXISTS `tv_shows`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tv_shows` (
  `idShow` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `overview` text COLLATE utf8_unicode_ci DEFAULT NULL,
  `icon` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `fanart` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `rating` int(11) DEFAULT NULL,
  `premiered` date DEFAULT NULL,
  `genre` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `scraperName` char(10) COLLATE utf8_unicode_ci DEFAULT NULL,
  `scraperID` int(11) DEFAULT NULL,
  `path` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `multipleResults` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `forceUpdate` tinyint(4) NOT NULL DEFAULT 0,
  PRIMARY KEY (`idShow`)
) ENGINE=InnoDB AUTO_INCREMENT=72 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `users` (
  `idUser` int(11) NOT NULL AUTO_INCREMENT,
  `token` text COLLATE utf8_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `icon` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `user` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `password` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `admin` tinyint(1) unsigned zerofill NOT NULL,
  `kodiLinkBase` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`idUser`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'jrfttgnfghtser4gs6dgt586es6984g','Droso','bogruf.jpg','Thomas','58d34a370cf4b30921dcf3e29c4db1790fbffb0127cfb7ffcdd783f373a4bbc8',1,'ThomasVideo116');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `views`
--

DROP TABLE IF EXISTS `views`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `views` (
  `idView` int(11) NOT NULL AUTO_INCREMENT,
  `idUser` int(11) NOT NULL,
  `idShow` int(11) DEFAULT NULL,
  `idEpisode` int(11) DEFAULT NULL,
  `viewCount` int(10) unsigned zerofill NOT NULL,
  PRIMARY KEY (`idView`),
  KEY `idUser` (`idUser`),
  KEY `idShow` (`idShow`),
  KEY `idEpisode` (`idEpisode`),
  CONSTRAINT `views_ibfk_1` FOREIGN KEY (`idUser`) REFERENCES `users` (`idUser`),
  CONSTRAINT `views_ibfk_2` FOREIGN KEY (`idShow`) REFERENCES `tv_shows` (`idShow`),
  CONSTRAINT `views_ibfk_3` FOREIGN KEY (`idEpisode`) REFERENCES `episodes` (`idEpisode`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `views`
--

LOCK TABLES `views` WRITE;
/*!40000 ALTER TABLE `views` DISABLE KEYS */;
/*!40000 ALTER TABLE `views` ENABLE KEYS */;
UNLOCK TABLES;