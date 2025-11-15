<?php
include __DIR__ . '/../config/db.php';
if (session_status() === PHP_SESSION_NONE) { session_start(); }
if (empty($_SESSION['user_id'])) { header('Location: ' . BASE_URL . 'auth/login.php'); exit; }

$cartId = isset($_POST['cart_id']) ? (int)$_POST['cart_id'] : 0;
if ($cartId <= 0) { header('Location: ' . BASE_URL . 'cart/cart.php'); exit; }

$del = $pdo->prepare('DELETE FROM cart WHERE id = ? AND user_id = ?');
$del->execute([$cartId, (int)$_SESSION['user_id']]);
header('Location: ' . BASE_URL . 'cart/cart.php');
exit;