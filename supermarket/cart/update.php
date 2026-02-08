<?php
include __DIR__ . '/../config/db.php';
if (session_status() === PHP_SESSION_NONE) { session_start(); }
if (empty($_SESSION['user_id'])) { header('Location: ' . BASE_URL . 'auth/login.php'); exit; }

$cartId = isset($_POST['cart_id']) ? (int)$_POST['cart_id'] : 0;
$quantity = isset($_POST['quantity']) ? (int)$_POST['quantity'] : 1;
if ($cartId <= 0 || $quantity <= 0) { header('Location: ' . BASE_URL . 'cart/cart.php'); exit; }

$upd = $pdo->prepare('UPDATE cart SET quantity = ? WHERE id = ? AND user_id = ?');
$upd->execute([$quantity, $cartId, (int)$_SESSION['user_id']]);
header('Location: ' . BASE_URL . 'cart/cart.php');
exit;