-- Adminer 4.7.8 MySQL dump

SET NAMES utf8;
SET time_zone = '+00:00';
SET foreign_key_checks = 0;

DROP DATABASE IF EXISTS `zogwine`;
CREATE DATABASE `zogwine` /*!40100 DEFAULT CHARACTER SET utf8 */;
USE `zogwine`;

DROP TABLE IF EXISTS `devices`;
CREATE TABLE `devices` (
  `idDevice` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `type` varchar(255) NOT NULL,
  `address` varchar(255) NOT NULL,
  `port` int(11) DEFAULT NULL,
  `user` varchar(255) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `device` text DEFAULT NULL,
  `enabled` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`idDevice`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `episodes`;
CREATE TABLE `episodes` (
  `idEpisode` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) DEFAULT NULL,
  `overview` text DEFAULT NULL,
  `icon` varchar(255) DEFAULT NULL,
  `premiered` varchar(255) DEFAULT NULL,
  `season` int(11) DEFAULT NULL,
  `episode` int(11) DEFAULT NULL,
  `rating` int(11) DEFAULT NULL,
  `scraperName` char(10) DEFAULT NULL,
  `scraperID` int(11) DEFAULT NULL,
  `scraperData` text DEFAULT NULL,
  `scraperLink` text DEFAULT NULL,
  `filler` int(11) DEFAULT 0,
  `idShow` int(11) DEFAULT NULL,
  `idVid` int(11) DEFAULT NULL,
  `addDate` int(11) DEFAULT NULL,
  `updateDate` int(11) DEFAULT NULL,
  `forceUpdate` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`idEpisode`),
  KEY `idShow` (`idShow`),
  KEY `idVid` (`idVid`),
  CONSTRAINT `episodes_ibfk_1` FOREIGN KEY (`idShow`) REFERENCES `tv_shows` (`idShow`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `fillers`;
CREATE TABLE `fillers` (
  `mediaType` int(11) NOT NULL,
  `mediaData` int(11) NOT NULL,
  `fillerType` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `libraries`;
CREATE TABLE `libraries` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `path` text NOT NULL,
  `mediaType` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `movies`;
CREATE TABLE `movies` (
  `idMovie` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) DEFAULT NULL,
  `overview` text DEFAULT NULL,
  `icon` varchar(255) DEFAULT NULL,
  `fanart` varchar(255) DEFAULT NULL,
  `rating` varchar(255) DEFAULT NULL,
  `premiered` varchar(255) DEFAULT NULL,
  `idCollection` int(11) DEFAULT NULL,
  `scraperName` char(10) DEFAULT NULL,
  `scraperID` int(10) DEFAULT NULL,
  `scraperData` varchar(255) DEFAULT NULL,
  `scraperLink` text DEFAULT NULL,
  `idVid` int(11) DEFAULT NULL,
  `addDate` int(11) DEFAULT NULL,
  `updateDate` int(11) DEFAULT NULL,
  `forceUpdate` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`idMovie`),
  KEY `idCollection` (`idCollection`),
  KEY `idVid` (`idVid`),
  CONSTRAINT `movies_ibfk_1` FOREIGN KEY (`idCollection`) REFERENCES `movie_collections` (`idCollection`),
  CONSTRAINT `movies_ibfk_2` FOREIGN KEY (`idVid`) REFERENCES `video_files` (`idVid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `movie_collections`;
CREATE TABLE `movie_collections` (
  `idCollection` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) DEFAULT NULL,
  `overview` text DEFAULT NULL,
  `premiered` varchar(255) DEFAULT NULL,
  `icon` text DEFAULT NULL,
  `fanart` text DEFAULT NULL,
  `scraperName` varchar(255) NOT NULL,
  `scraperID` int(11) NOT NULL,
  `scraperData` text DEFAULT NULL,
  `scraperLink` text DEFAULT NULL,
  `forceUpdate` tinyint(4) NOT NULL DEFAULT 0,
  `addDate` int(11) NOT NULL,
  `updateDate` int(11) NOT NULL,
  PRIMARY KEY (`idCollection`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `people`;
CREATE TABLE `people` (
  `idPers` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `gender` int(11) DEFAULT NULL,
  `birthdate` date DEFAULT NULL,
  `deathdate` date DEFAULT NULL,
  `description` text DEFAULT NULL,
  `icon` text DEFAULT NULL,
  `known_for` varchar(255) DEFAULT NULL,
  `updateDate` int(11) NOT NULL,
  `addDate` int(11) NOT NULL,
  `scraperName` varchar(255) DEFAULT NULL,
  `scraperID` varchar(255) DEFAULT NULL,
  `scraperData` text DEFAULT NULL,
  `scraperLink` text DEFAULT NULL,
  `forceUpdate` tinyint(4) NOT NULL DEFAULT 0,
  PRIMARY KEY (`idPers`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `people_link`;
CREATE TABLE `people_link` (
  `idPers` int(11) NOT NULL,
  `idMedia` int(11) NOT NULL,
  `mediaType` int(11) NOT NULL,
  `role` varchar(255) NOT NULL,
  KEY `idPers` (`idPers`),
  CONSTRAINT `people_link_ibfk_1` FOREIGN KEY (`idPers`) REFERENCES `people` (`idPers`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `role`;
CREATE TABLE `role` (
  `idRole` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `forceUpdate` int(11) NOT NULL,
  PRIMARY KEY (`idRole`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `role_link`;
CREATE TABLE `role_link` (
  `mediaType` int(11) NOT NULL,
  `mediaData` text NOT NULL,
  `idPers` int(11) NOT NULL,
  `idRole` int(11) NOT NULL,
  KEY `idPers` (`idPers`),
  KEY `idRole` (`idRole`),
  CONSTRAINT `role_link_ibfk_1` FOREIGN KEY (`idPers`) REFERENCES `people` (`idPers`),
  CONSTRAINT `role_link_ibfk_2` FOREIGN KEY (`idRole`) REFERENCES `role` (`idRole`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `scrapers`;
CREATE TABLE `scrapers` (
  `providerName` varchar(255) NOT NULL,
  `priority` int(11) NOT NULL,
  `mediaTypes` varchar(255) NOT NULL,
  `settings` text NOT NULL,
  `enabled` tinyint(4) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `seasons`;
CREATE TABLE `seasons` (
  `idShow` int(11) NOT NULL,
  `season` int(11) NOT NULL,
  `title` varchar(255) NOT NULL,
  `overview` text DEFAULT NULL,
  `icon` text DEFAULT NULL,
  `premiered` varchar(255) DEFAULT NULL,
  `rating` int(11) DEFAULT NULL,
  `scraperName` char(10) DEFAULT NULL,
  `scraperID` int(11) DEFAULT NULL,
  `scraperData` text DEFAULT NULL,
  `scraperLink` text DEFAULT NULL,
  `addDate` int(11) DEFAULT NULL,
  `updateDate` int(11) DEFAULT NULL,
  `forceUpdate` tinyint(4) NOT NULL,
  KEY `idShow` (`idShow`),
  KEY `season` (`season`),
  CONSTRAINT `seasons_ibfk_1` FOREIGN KEY (`idShow`) REFERENCES `tv_shows` (`idShow`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `selections`;
CREATE TABLE `selections` (
  `mediaType` int(11) NOT NULL,
  `mediaData` text NOT NULL,
  `data` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `status`;
CREATE TABLE `status` (
  `idStatus` int(11) NOT NULL AUTO_INCREMENT,
  `idUser` int(11) NOT NULL,
  `idMedia` int(11) NOT NULL,
  `mediaType` int(11) NOT NULL,
  `watchCount` int(11) NOT NULL DEFAULT 0,
  `watchTime` int(11) NOT NULL DEFAULT 0,
  `lastDate` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`idStatus`),
  KEY `idUser` (`idUser`),
  CONSTRAINT `status_ibfk_1` FOREIGN KEY (`idUser`) REFERENCES `users` (`idUser`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `tags`;
CREATE TABLE `tags` (
  `idTag` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `value` varchar(255) NOT NULL,
  `icon` text DEFAULT NULL,
  PRIMARY KEY (`idTag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `tags_link`;
CREATE TABLE `tags_link` (
  `idTag` int(11) NOT NULL,
  `idMedia` int(11) NOT NULL,
  `mediaType` int(11) NOT NULL,
  KEY `idTag` (`idTag`),
  CONSTRAINT `tags_link_ibfk_1` FOREIGN KEY (`idTag`) REFERENCES `tags` (`idTag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `trackers`;
CREATE TABLE `trackers` (
  `idTracker` int(11) NOT NULL AUTO_INCREMENT,
  `idUser` int(11) NOT NULL,
  `name` varchar(255) NOT NULL,
  `type` varchar(255) NOT NULL,
  `user` text DEFAULT NULL,
  `password` text DEFAULT NULL,
  `address` text DEFAULT NULL,
  `port` int(11) DEFAULT NULL,
  `data` text DEFAULT NULL,
  `direction` int(11) NOT NULL,
  `syncTypes` text NOT NULL,
  `enabled` tinyint(4) NOT NULL,
  KEY `idTracker` (`idTracker`),
  KEY `idUser` (`idUser`),
  CONSTRAINT `trackers_ibfk_2` FOREIGN KEY (`idUser`) REFERENCES `users` (`idUser`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `trackers_link`;
CREATE TABLE `trackers_link` (
  `mediaType` int(11) NOT NULL,
  `mediaData` text NOT NULL,
  `idTracker` int(11) NOT NULL,
  `trackerData` text NOT NULL,
  `enabled` tinyint(4) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `tv_shows`;
CREATE TABLE `tv_shows` (
  `idShow` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) DEFAULT NULL,
  `overview` text DEFAULT NULL,
  `icon` varchar(255) DEFAULT NULL,
  `fanart` varchar(255) DEFAULT NULL,
  `rating` int(11) DEFAULT NULL,
  `premiered` varchar(255) DEFAULT NULL,
  `scraperName` char(10) DEFAULT NULL,
  `scraperID` int(11) DEFAULT NULL,
  `scraperData` varchar(255) DEFAULT NULL,
  `scraperLink` text DEFAULT NULL,
  `fillerLink` text DEFAULT NULL,
  `path` varchar(255) DEFAULT NULL,
  `idLib` int(11) DEFAULT NULL,
  `selectedResult` tinyint(4) DEFAULT NULL,
  `updateDate` int(11) DEFAULT NULL,
  `addDate` int(11) DEFAULT NULL,
  `forceUpdate` tinyint(4) NOT NULL DEFAULT 0,
  PRIMARY KEY (`idShow`),
  KEY `idLib` (`idLib`),
  CONSTRAINT `tv_shows_ibfk_1` FOREIGN KEY (`idLib`) REFERENCES `libraries` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `upcoming`;
CREATE TABLE `upcoming` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `mediaType` int(2) NOT NULL,
  `refMediaData` varchar(255) DEFAULT NULL,
  `title` varchar(255) NOT NULL,
  `overview` text DEFAULT NULL,
  `icon` varchar(255) DEFAULT NULL,
  `date` date NOT NULL,
  `id_1` int(11) DEFAULT NULL,
  `id_2` int(11) DEFAULT NULL,
  PRIMARY KEY (`mediaType`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `idUser` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `user` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `admin` tinyint(1) unsigned zerofill NOT NULL DEFAULT 0,
  `cast` tinyint(1) unsigned zerofill NOT NULL DEFAULT 0,
  `receive` tinyint(1) unsigned zerofill NOT NULL DEFAULT 0,
  `indexof` tinyint(1) unsigned zerofill NOT NULL DEFAULT 0,
  `allowMovie` tinyint(1) unsigned zerofill NOT NULL DEFAULT 1,
  `allowTvs` tinyint(1) unsigned zerofill NOT NULL DEFAULT 1,
  PRIMARY KEY (`idUser`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `video_files`;
CREATE TABLE `video_files` (
  `idVid` int(11) NOT NULL AUTO_INCREMENT,
  `idLib` int(11) NOT NULL,
  `path` text NOT NULL,
  `format` varchar(255) DEFAULT NULL,
  `duration` float NOT NULL,
  `extension` varchar(10) NOT NULL,
  `audio` longtext NOT NULL,
  `subtitles` longtext DEFAULT NULL,
  `stereo3d` tinyint(4) NOT NULL DEFAULT 0,
  `ratio` varchar(20) DEFAULT NULL,
  `dimension` varchar(50) DEFAULT NULL,
  `pix_fmt` varchar(50) DEFAULT NULL,
  `video_codec` varchar(50) DEFAULT NULL,
  `size` bigint(20) NOT NULL,
  PRIMARY KEY (`idVid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


-- 2021-11-21 21:41:20
