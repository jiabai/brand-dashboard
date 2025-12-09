-- MySQL 建表语句
-- 品牌分析API数据库架构

-- Q&A品牌状态记录表
CREATE TABLE `qa_brand_state` ( 
   `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT 'Auto-increment primary key', 
   `date` date NOT NULL COMMENT 'Date of the record', 
   `question_id` varchar(64) NOT NULL COMMENT 'Unique identifier for the question', 
   `brand` varchar(100) NOT NULL COMMENT 'Brand name mentioned', 
   `product` varchar(255) DEFAULT NULL COMMENT 'Product name or description (optional)', 
   `platform` varchar(100) NOT NULL COMMENT 'Platform where the question was posted (e.g., Qwen, Deepseek, etc.)', 
   `question` text NOT NULL COMMENT 'The user''s original question', 
   `answer` text NOT NULL COMMENT 'The provided answer', 
   `is_mentioned` tinyint(1) NOT NULL DEFAULT '0' COMMENT 'Whether the brand is mentioned in the answer (0 = no, 1 = yes)', 
   `is_first_mention` tinyint(1) NOT NULL DEFAULT '0' COMMENT 'Whether the brand is the first mentioned in the answer', 
   `sentiment_status` varchar(20) NOT NULL COMMENT 'Sentiment/emotion status (e.g., positive, negative, neutral)', 
   `brands_found` json DEFAULT NULL COMMENT 'All brands found in the text (e.g., ["海尔 (Haier)", ...])', 
   PRIMARY KEY (`id`), 
   KEY `idx_date` (`date`), 
   KEY `idx_question_id` (`question_id`), 
   KEY `idx_brand` (`brand`), 
   KEY `idx_platform` (`platform`), 
   KEY `idx_sentiment_status` (`sentiment_status`) 
 ) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COMMENT='Records of brand status in Q&A';

-- Q&A品牌汇总统计表
CREATE TABLE `qa_brand_summary` ( 
   `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT 'Auto-increment ID', 
   `date` date NOT NULL COMMENT 'Summary date (e.g., daily)', 
   `brand` varchar(100) NOT NULL COMMENT 'Brand name', 
   `product` varchar(255) DEFAULT NULL COMMENT 'Product name (optional)', 
   `platform` varchar(100) NOT NULL COMMENT 'Platform (e.g., Qwen, Deepseek)', 
   `question_count` int(11) NOT NULL COMMENT 'Total number of questions', 
   `mention_count` int(11) NOT NULL COMMENT 'Total mentions of the brand', 
   `first_mention_count` int(11) NOT NULL COMMENT 'Number of first-time mentions', 
   `mention_rate` decimal(5,2) NOT NULL COMMENT 'Mention rate (e.g., 0.85 for 85%)', 
   `first_mention_rate` decimal(5,2) NOT NULL COMMENT 'First mention rate (e.g., 0.30 for 30%)', 
   `positive_count` int(11) NOT NULL COMMENT 'Number of positive sentiment questions', 
   `negative_count` int(11) NOT NULL COMMENT 'Number of negative sentiment questions', 
   `positive_ratio` decimal(5,2) NOT NULL COMMENT 'Positive sentiment ratio (e.g., 0.70 for 70%)', 
   `negative_ratio` decimal(5,2) NOT NULL COMMENT 'Negative sentiment ratio (e.g., 0.25 for 25%)', 
   PRIMARY KEY (`id`), 
   KEY `idx_date_brand` (`date`,`brand`), 
   KEY `idx_platform` (`platform`), 
   KEY `idx_brand_product` (`brand`,`product`) 
 ) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COMMENT='Daily brand sentiment and mention statistics summary';

-- Q&A参考链接表
CREATE TABLE `qa_reference` ( 
   `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT 'Auto-increment primary key', 
   `date` date NOT NULL COMMENT 'Date of the question', 
   `question_id` varchar(64) NOT NULL COMMENT 'Unique identifier for the question', 
   `brand` varchar(100) NOT NULL COMMENT 'Brand name', 
   `product` varchar(255) NOT NULL COMMENT 'Product name or description', 
   `platform` varchar(100) NOT NULL COMMENT 'Platform (e.g., Taobao, JD, etc.)', 
   `answer_reference_url` text COMMENT 'URL referenced in the answer', 
   `search_url` text COMMENT 'Original URL used to retrieve the question', 
   PRIMARY KEY (`id`), 
   KEY `idx_date` (`date`), 
   KEY `idx_question_id` (`question_id`), 
   KEY `idx_brand` (`brand`), 
   KEY `idx_platform` (`platform`) 
 ) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COMMENT='Table storing Q&A reference with metadata';

