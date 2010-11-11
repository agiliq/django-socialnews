
-- length of news_topic.name is 100
ALTER TABLE `news_topic` ADD COLUMN slug VARCHAR(100) NOT NULL;

ALTER TABLE `news_link` ADD COLUMN summary VARCHAR(255) NOT NULL;
ALTER TABLE `news_link` ADD COLUMN slug VARCHAR(255) NOT NULL;
