-- MySQL dump 10.13  Distrib 5.1.73, for debian-linux-gnu (i486)
--
-- Host: localhost    Database: DB_ACB
-- ------------------------------------------------------
-- Server version	5.1.73-0ubuntu0.10.04.1-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `T_ADMINISTRATOR`
--

DROP TABLE IF EXISTS `T_ADMINISTRATOR`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `T_ADMINISTRATOR` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `login` varchar(20) NOT NULL,
  `password` varchar(64) NOT NULL,
  `name` varchar(40) NOT NULL,
  `mobile` varchar(20) NOT NULL,
  `phone` varchar(20) NOT NULL,
  `email` varchar(40) NOT NULL,
  `corporation` varchar(100) NOT NULL,
  `source_id` int(10) unsigned DEFAULT '5' COMMENT '账号的来源：省移动公司，139，市移动公司等。',
  `valid` tinyint(4) NOT NULL DEFAULT '1' COMMENT '1：启用；\n0：停用。',
  `type` char(1) NOT NULL DEFAULT '1' COMMENT '0:超级管理员；1：普通业务管理员(校讯通同步来的);2:市级管理员(admin新增的)',
  `is_ajt` tinyint(1) unsigned NOT NULL DEFAULT '0' COMMENT '是否为安捷通用户。 0: 移动卫士； 1：安捷通',
  PRIMARY KEY (`id`),
  UNIQUE KEY `login_UNIQUE` (`login`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8 COMMENT='后台管理员表。';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `T_ADMINISTRATOR`
--

LOCK TABLES `T_ADMINISTRATOR` WRITE;
/*!40000 ALTER TABLE `T_ADMINISTRATOR` DISABLE KEYS */;
INSERT INTO `T_ADMINISTRATOR` VALUES (1,'admin','*CF749C58F22D071761519131B550F65FA004B2F9','超级管理员','','','','',5,1,'1',0),(4,'chenshi','*FD571203974BA9AFE270FE62151AE967ECA5E0AA','陈实','','','','',5,1,'2',0),(5,'denglei','*FD571203974BA9AFE270FE62151AE967ECA5E0AA','邓磊','','','','',5,1,'2',0),(6,'huanhui','*FD571203974BA9AFE270FE62151AE967ECA5E0AA','黄辉','','','','',5,1,'2',0),(7,'chenmengxuan','*FD571203974BA9AFE270FE62151AE967ECA5E0AA','陈孟轩','','','','',5,1,'2',0),(15,'lipan','*FD571203974BA9AFE270FE62151AE967ECA5E0AA','李攀','','','','',2,1,'2',0),(16,'ajtadmin','*FD571203974BA9AFE270FE62151AE967ECA5E0AA','安捷通管理员','','','','',5,1,'2',1),(20,'jiatest','*FD571203974BA9AFE270FE62151AE967ECA5E0AA','jiatest','','','','',5,1,'2',0),(23,'chenmengxua','*FD571203974BA9AFE270FE62151AE967ECA5E0AA','陈孟轩','','','','',5,1,'2',0),(24,'liuqi','*FD571203974BA9AFE270FE62151AE967ECA5E0AA','刘琦','','','','',5,1,'2',0);
/*!40000 ALTER TABLE `T_ADMINISTRATOR` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `T_META_PRIVILEGE`
--

DROP TABLE IF EXISTS `T_META_PRIVILEGE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `T_META_PRIVILEGE` (
  `id` int(10) unsigned NOT NULL,
  `name` varchar(100) NOT NULL DEFAULT '' COMMENT '基本权限表。每种权限的名字和id事先指定好，在程序中便于对应。',
  `mnemonic` varchar(100) NOT NULL COMMENT '??????',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_UNIQUE` (`name`),
  UNIQUE KEY `mnemonic_UNIQUE` (`mnemonic`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='后台管理员权限表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `T_META_PRIVILEGE`
--

LOCK TABLES `T_META_PRIVILEGE` WRITE;
/*!40000 ALTER TABLE `T_META_PRIVILEGE` DISABLE KEYS */;
INSERT INTO `T_META_PRIVILEGE` VALUES (1,'查询后台用户','QUERY_ADMINISTRATOR'),(2,'查看用户信息','LIST_ADMINISTRATOR'),(3,'编辑后台用户','EDIT_ADMINISTRATOR'),(4,'新建后台用户','CREATE_ADMINISTRATOR'),(5,'删除后台用户','DELETE_ADMINISTRATOR'),(6,'重置用户密码','RESET_OTHER_PASSWORD'),(7,'修改自己密码','RESET_MY_PASSWORD'),(8,'权限组管理','MANAGE_PRIVILEGE_GROUP'),(9,'代客操作','DELEGATION'),(10,'业务受理','BUSINESS_HANDLE'),(11,'业务查询','BUSINESS_QUERY'),(12,'个人业务查询','QUERY_BUSINESS'),(13,'个人业务受理','CREATE_BUSINESS'),(14,'查看个人用户','LIST_BUSINESS'),(15,'编辑个人用户','EDIT_BUSINESS'),(16,'删除个人用户','DELETE_BUSINESS'),(17,'终端信息查询','TERMINAL_QUERY'),(18,'报表统计','STATISTIC'),(19,'白名单','WHITELIST'),(20,'活动管理','ACTIVITY'),(21,'APK管理','APK');
/*!40000 ALTER TABLE `T_META_PRIVILEGE` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `T_PRIVILEGE`
--

DROP TABLE IF EXISTS `T_PRIVILEGE`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `T_PRIVILEGE` (
  `administrator_id` int(10) unsigned NOT NULL,
  `privilege_group_id` int(10) unsigned NOT NULL DEFAULT '20',
  PRIMARY KEY (`administrator_id`,`privilege_group_id`),
  KEY `group_priv_admin_id` (`administrator_id`),
  KEY `group_priv_group_id` (`privilege_group_id`),
  CONSTRAINT `group_priv_admin_id` FOREIGN KEY (`administrator_id`) REFERENCES `T_ADMINISTRATOR` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `group_priv_group_id` FOREIGN KEY (`privilege_group_id`) REFERENCES `T_PRIVILEGE_GROUP` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='后台用户所对应的权限组。非权限组用户的权限在T_PRIVILEGE中。请注意与T_PRIVILEGE_GROUP的区别。';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `T_PRIVILEGE`
--

LOCK TABLES `T_PRIVILEGE` WRITE;
/*!40000 ALTER TABLE `T_PRIVILEGE` DISABLE KEYS */;
INSERT INTO `T_PRIVILEGE` VALUES (1,26),(4,32),(4,33),(4,34),(4,35),(4,36),(4,37),(4,38),(4,39),(5,32),(5,33),(5,34),(5,35),(5,36),(5,37),(5,38),(5,39),(6,32),(6,34),(6,37),(6,38),(6,39),(7,32),(7,34),(7,36),(7,39),(15,31),(16,36),(20,31),(23,32),(23,33),(23,34),(23,36),(24,32),(24,33),(24,34),(24,35),(24,36),(24,39);
/*!40000 ALTER TABLE `T_PRIVILEGE` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `T_PRIVILEGE_GROUP`
--

DROP TABLE IF EXISTS `T_PRIVILEGE_GROUP`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `T_PRIVILEGE_GROUP` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL COMMENT '权限组的名字。',
  `builtin` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否为基本权限映射过来的组。这些组不得删除。',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_UNIQUE` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=40 DEFAULT CHARSET=utf8 COMMENT='权限组。';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `T_PRIVILEGE_GROUP`
--

LOCK TABLES `T_PRIVILEGE_GROUP` WRITE;
/*!40000 ALTER TABLE `T_PRIVILEGE_GROUP` DISABLE KEYS */;
INSERT INTO `T_PRIVILEGE_GROUP` VALUES (26,'超级权限',0),(31,'系统管理',0),(32,'代客操作',0),(33,'业务受理',0),(34,'终端信息查询',0),(35,'报表统计',0),(36,'白名单',0),(37,'活动管理',0),(38,'APK管理',0),(39,'业务查询',0);
/*!40000 ALTER TABLE `T_PRIVILEGE_GROUP` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `T_PRIVILEGE_GROUP_DATA`
--

DROP TABLE IF EXISTS `T_PRIVILEGE_GROUP_DATA`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `T_PRIVILEGE_GROUP_DATA` (
  `privilege_group_id` int(10) unsigned NOT NULL,
  `privilege_id` int(10) unsigned NOT NULL,
  PRIMARY KEY (`privilege_group_id`,`privilege_id`),
  KEY `group_data_group_id` (`privilege_group_id`),
  KEY `group_data_priv_id` (`privilege_id`),
  CONSTRAINT `group_data_group_id` FOREIGN KEY (`privilege_group_id`) REFERENCES `T_PRIVILEGE_GROUP` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='权限组的包含的具体权限列表。';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `T_PRIVILEGE_GROUP_DATA`
--

LOCK TABLES `T_PRIVILEGE_GROUP_DATA` WRITE;
/*!40000 ALTER TABLE `T_PRIVILEGE_GROUP_DATA` DISABLE KEYS */;
INSERT INTO `T_PRIVILEGE_GROUP_DATA` VALUES (26,1),(26,2),(26,3),(26,4),(26,5),(26,6),(26,7),(26,8),(26,9),(26,10),(26,11),(26,12),(26,13),(26,14),(26,15),(26,16),(26,17),(26,18),(26,19),(26,20),(26,21),(26,22),(26,23),(26,24),(26,25),(31,1),(31,2),(31,3),(31,4),(31,5),(31,6),(31,8),(32,9),(33,10),(34,17),(35,18),(36,19),(37,20),(38,21),(39,11);
/*!40000 ALTER TABLE `T_PRIVILEGE_GROUP_DATA` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2014-04-24 20:46:08
