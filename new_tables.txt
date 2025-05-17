CREATE TABLE `stockmanegement`.`acik_hesap` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `number` varchar(255) NOT NULL,
  `products` varchar(255) NOT NULL,
  `start_price` int NOT NULL,
  `remaining_price` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `kur` varchar(30) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;



CREATE TABLE `stockmanegement`.`acik_hesap_odeme` (
  `odeme_id` int NOT NULL AUTO_INCREMENT,
  `hesap_id` int NOT NULL,
  `payment` int NOT NULL,
  `payment_type` varchar(255) NOT NULL,
  `start_price` int NOT NULL,
  `remaining_price` int NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `kur` varchar(30) DEFAULT NULL,
  PRIMARY KEY (`odeme_id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
