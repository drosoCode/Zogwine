-- Adminer 4.7.7 MySQL dump

SET NAMES utf8;
SET time_zone = '+00:00';
SET foreign_key_checks = 0;
SET sql_mode = 'NO_AUTO_VALUE_ON_ZERO';

CREATE DATABASE `zogwine_dev` /*!40100 DEFAULT CHARACTER SET utf8 */;
USE `zogwine_dev`;

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
  `season` int(11) DEFAULT NULL,
  `episode` int(11) DEFAULT NULL,
  `rating` int(11) DEFAULT NULL,
  `scraperName` char(10) DEFAULT NULL,
  `scraperID` int(11) DEFAULT NULL,
  `scraperData` text DEFAULT NULL,
  `filler` int(11) DEFAULT 0,
  `idShow` int(11) DEFAULT NULL,
  `idVid` int(11) DEFAULT NULL,
  `addDate` datetime DEFAULT NULL ON UPDATE current_timestamp(),
  `forceUpdate` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`idEpisode`),
  KEY `idShow` (`idShow`),
  KEY `idVid` (`idVid`),
  CONSTRAINT `episodes_ibfk_1` FOREIGN KEY (`idShow`) REFERENCES `tv_shows` (`idShow`),
  CONSTRAINT `episodes_ibfk_2` FOREIGN KEY (`idVid`) REFERENCES `video_files` (`idVid`)
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
  `idVid` int(11) DEFAULT NULL,
  `addDate` datetime DEFAULT NULL ON UPDATE current_timestamp(),
  `multipleResults` longtext DEFAULT NULL,
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
  `forceUpdate` tinyint(4) NOT NULL DEFAULT 0,
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


DROP TABLE IF EXISTS `scrapers`;
CREATE TABLE `scrapers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `scraperName` varchar(255) NOT NULL,
  `scraperURL` varchar(255) NOT NULL,
  `mediaType` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

INSERT INTO `scrapers` (`id`, `scraperName`, `scraperURL`, `mediaType`) VALUES
(1,	'tmdb',	'https://www.themoviedb.org/tv/',	1),
(2,	'tvdb',	'https://thetvdb.com/?tab=series&id=',	1),
(3,	'imdb',	'https://www.imdb.com/title/',	1),
(4,	'tmdb',	'https://www.themoviedb.org/movie/',	3);

DROP TABLE IF EXISTS `seasons`;
CREATE TABLE `seasons` (
  `idShow` int(11) NOT NULL,
  `season` int(11) NOT NULL,
  `title` varchar(255) NOT NULL,
  `overview` text DEFAULT NULL,
  `icon` text DEFAULT NULL,
  `premiered` varchar(255) DEFAULT NULL,
  `forceUpdate` tinyint(4) NOT NULL,
  KEY `idShow` (`idShow`),
  KEY `season` (`season`),
  CONSTRAINT `seasons_ibfk_1` FOREIGN KEY (`idShow`) REFERENCES `tv_shows` (`idShow`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `status`;
CREATE TABLE `status` (
  `idStatus` int(11) NOT NULL AUTO_INCREMENT,
  `idUser` int(11) NOT NULL,
  `idMedia` int(11) NOT NULL,
  `mediaType` int(11) NOT NULL,
  `watchCount` int(11) NOT NULL DEFAULT 0,
  `watchTime` int(11) NOT NULL DEFAULT 0,
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


DROP TABLE IF EXISTS `tv_shows`;
CREATE TABLE `tv_shows` (
  `idShow` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) DEFAULT NULL,
  `overview` text DEFAULT NULL,
  `icon` varchar(255) DEFAULT NULL,
  `fanart` varchar(255) DEFAULT NULL,
  `rating` int(11) DEFAULT NULL,
  `premiered` date DEFAULT NULL,
  `scraperName` char(10) DEFAULT NULL,
  `scraperID` int(11) DEFAULT NULL,
  `scraperData` varchar(255) DEFAULT NULL,
  `fillerLink` text DEFAULT NULL,
  `path` varchar(255) DEFAULT NULL,
  `multipleResults` longtext DEFAULT NULL,
  `forceUpdate` tinyint(4) NOT NULL DEFAULT 0,
  PRIMARY KEY (`idShow`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `upcoming_episodes`;
CREATE TABLE `upcoming_episodes` (
  `idEpisode` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) DEFAULT NULL,
  `overview` text DEFAULT NULL,
  `season` int(11) DEFAULT NULL,
  `episode` int(11) DEFAULT NULL,
  `date` date DEFAULT NULL,
  `icon` varchar(255) DEFAULT NULL,
  `idShow` int(11) NOT NULL,
  PRIMARY KEY (`idEpisode`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `idUser` int(11) NOT NULL AUTO_INCREMENT,
  `token` text NOT NULL,
  `name` varchar(255) NOT NULL,
  `icon` varchar(255) NOT NULL,
  `user` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `admin` tinyint(1) unsigned zerofill NOT NULL,
  `cast` tinyint(1) unsigned zerofill NOT NULL,
  `kodiLinkBase` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`idUser`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `video_files`;
CREATE TABLE `video_files` (
  `idVid` int(11) NOT NULL AUTO_INCREMENT,
  `mediaType` int(11) NOT NULL,
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


-- 2020-11-25 14:56:37
