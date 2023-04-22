DROP TABLE IF EXISTS study_programs;

CREATE TABLE study_programs (
    id INT PRIMARY KEY NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    degree VARCHAR(10) NOT NULL,
    language VARCHAR(2) NOT NULL,
    ...
)