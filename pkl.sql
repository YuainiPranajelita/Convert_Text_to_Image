-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jul 29, 2024 at 06:48 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `pkl`
--

DELIMITER $$
--
-- Procedures
--
CREATE DEFINER=`root`@`localhost` PROCEDURE `CekKodeBuku` (IN `kode_buku` VARCHAR(100), IN `paket` INT)   BEGIN
    
        SELECT kode_buku FROM paket WHERE kode_buku LIKE CONCAT('%', kode_buku, '%');
END$$

DELIMITER ;

-- --------------------------------------------------------

--
-- Table structure for table `paket`
--

CREATE TABLE `paket` (
  `id` int(11) NOT NULL,
  `paket` int(11) NOT NULL,
  `kode_buku` varchar(100) NOT NULL,
  `judul_buku` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `paket`
--

INSERT INTO `paket` (`id`, `paket`, `kode_buku`, `judul_buku`) VALUES
(1, 1, 'ADBI4331', 'Uang dan Perbankan'),
(2, 1, 'ADBI4440', 'Kewirausahaan'),
(3, 1, 'EKMA4214', 'Manajemen Sumber Daya Manusia'),
(4, 1, 'EKMA4311', 'Studi Kelayakan Bisnis'),
(5, 1, 'EKS14205', 'Bank dan Lembaga Keuangan Non Bank'),
(6, 1, 'ISIP4215', 'Pengantar Statistik Sosial'),
(7, 1, 'ISIP4216', 'Metode Penelitian Sosial'),
(8, 2, 'ADBI4130', 'Pengantar Ilmu Administrasi Negara'),
(9, 2, 'ADBI4441', 'Praktik Bisnis di Indonesia'),
(10, 2, 'ADBI4449', 'Filsafat Bisnis'),
(11, 2, 'ADBU4442', 'Sistem Informasi Manajemen'),
(12, 2, 'ISIP4212', 'Pengantar Ilmu Politik'),
(13, 2, 'ISIP4213', 'Sistem Politik Indonesia');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `paket`
--
ALTER TABLE `paket`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `paket`
--
ALTER TABLE `paket`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=14;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
