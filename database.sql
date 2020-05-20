-- Adminer 4.7.6 MySQL dump

SET NAMES utf8;
SET time_zone = '+00:00';
SET foreign_key_checks = 0;
SET sql_mode = 'NO_AUTO_VALUE_ON_ZERO';

DROP DATABASE IF EXISTS `mediaController`;
CREATE DATABASE `mediaController` /*!40100 DEFAULT CHARACTER SET utf8 COLLATE utf8_bin */;
USE `mediaController`;

DROP TABLE IF EXISTS `episodes`;
CREATE TABLE `episodes` (
  `idEpisode` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `overview` text COLLATE utf8_unicode_ci DEFAULT NULL,
  `icon` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `season` int(11) DEFAULT NULL,
  `episode` int(11) DEFAULT NULL,
  `rating` int(11) DEFAULT NULL,
  `scraperName` char(10) COLLATE utf8_unicode_ci DEFAULT NULL,
  `scraperID` int(11) DEFAULT NULL,
  `scaperData` int(11) DEFAULT NULL,
  `path` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `idShow` int(11) DEFAULT NULL,
  `forceUpdate` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`idEpisode`),
  KEY `idShow` (`idShow`),
  CONSTRAINT `episodes_ibfk_1` FOREIGN KEY (`idShow`) REFERENCES `tv_shows` (`idShow`)
) ENGINE=InnoDB AUTO_INCREMENT=16750 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;


DROP TABLE IF EXISTS `movies`;
CREATE TABLE `movies` (
  `idMovie` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) COLLATE utf8_bin DEFAULT NULL,
  `overview` text COLLATE utf8_bin DEFAULT NULL,
  `icon` varchar(255) COLLATE utf8_bin DEFAULT NULL,
  `fanart` varchar(255) COLLATE utf8_bin DEFAULT NULL,
  `rating` varchar(255) COLLATE utf8_bin DEFAULT NULL,
  `premiered` varchar(255) COLLATE utf8_bin DEFAULT NULL,
  `genre` varchar(255) COLLATE utf8_bin DEFAULT NULL,
  `scraperName` char(10) COLLATE utf8_bin DEFAULT NULL,
  `scraperID` int(10) DEFAULT NULL,
  `scraperData` varchar(255) COLLATE utf8_bin DEFAULT NULL,
  `path` varchar(255) COLLATE utf8_bin DEFAULT NULL,
  `multipleResults` longtext COLLATE utf8_bin DEFAULT NULL,
  `forceUpdate` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`idMovie`)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8 COLLATE=utf8_bin;


DROP TABLE IF EXISTS `mov_status`;
CREATE TABLE `mov_status` (
  `idView` int(11) NOT NULL AUTO_INCREMENT,
  `idUser` int(11) NOT NULL,
  `idMovie` int(11) NOT NULL,
  `viewCount` int(11) NOT NULL DEFAULT 0,
  `viewTime` float NOT NULL DEFAULT 0,
  PRIMARY KEY (`idView`),
  KEY `idUser` (`idUser`),
  KEY `idMovie` (`idMovie`),
  CONSTRAINT `mov_status_ibfk_1` FOREIGN KEY (`idUser`) REFERENCES `users` (`idUser`),
  CONSTRAINT `mov_status_ibfk_2` FOREIGN KEY (`idMovie`) REFERENCES `movies` (`idMovie`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_bin;


DROP TABLE IF EXISTS `scrapers`;
CREATE TABLE `scrapers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `scraperName` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `scraperURL` varchar(255) COLLATE utf8_unicode_ci NOT NULL,
  `dataType` varchar(10) COLLATE utf8_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;


DROP TABLE IF EXISTS `tvs_status`;
CREATE TABLE `tvs_status` (
  `idView` int(11) NOT NULL AUTO_INCREMENT,
  `idUser` int(11) NOT NULL,
  `idEpisode` int(11) DEFAULT NULL,
  `viewCount` int(10) unsigned zerofill NOT NULL,
  `viewTime` float NOT NULL DEFAULT 0,
  PRIMARY KEY (`idView`),
  KEY `idUser` (`idUser`),
  KEY `idEpisode` (`idEpisode`),
  CONSTRAINT `tvs_status_ibfk_1` FOREIGN KEY (`idUser`) REFERENCES `users` (`idUser`),
  CONSTRAINT `tvs_status_ibfk_3` FOREIGN KEY (`idEpisode`) REFERENCES `episodes` (`idEpisode`)
) ENGINE=InnoDB AUTO_INCREMENT=1590 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;


SET NAMES utf8mb4;

DROP TABLE IF EXISTS `tv_shows`;
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
  `scraperData` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `path` varchar(255) COLLATE utf8_unicode_ci DEFAULT NULL,
  `multipleResults` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL,
  `forceUpdate` tinyint(4) NOT NULL DEFAULT 0,
  PRIMARY KEY (`idShow`)
) ENGINE=InnoDB AUTO_INCREMENT=154 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;


DROP TABLE IF EXISTS `users`;
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
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;


-- 2020-05-20 19:05:43
