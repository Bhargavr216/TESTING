<?php
include __DIR__ . '/../config/db.php';
if (session_status() === PHP_SESSION_NONE) { session_start(); }
if (empty($_SESSION['user_id'])) {
    header('Location: ' . BASE_URL . 'auth/login.php');
    exit;
}

$productId = isset($_POST['product_id']) ? (int)$_POST['product_id'] : 0;
$quantity = isset($_POST['quantity']) ? (int)$_POST['quantity'] : 1;
if ($productId <= 0 || $quantity <= 0) {
    header('Location: ' . BASE_URL . 'products/index.php');
    exit;
}

$p = $pdo->prepare('SELECT id, stock FROM products WHERE id = ?');
$p->execute([$productId]);
$product = $p->fetch();
if (!$product) {
    header('Location: ' . BASE_URL . 'products/index.php');
    exit;
}

$userId = (int)$_SESSION['user_id'];
$existing = $pdo->prepare('SELECT id, quantity FROM cart WHERE user_id = ? AND product_id = ?');
$existing->execute([$userId, $productId]);
$row = $existing->fetch();

if ($row) {
    $newQty = $row['quantity'] + $quantity;
    $upd = $pdo->prepare('UPDATE cart SET quantity = ? WHERE id = ?');
    $upd->execute([$newQty, $row['id']]);
} else {
    $ins = $pdo->prepare('INSERT INTO cart(user_id, product_id, quantity) VALUES(?,?,?)');
    $ins->execute([$userId, $productId, $quantity]);
}

header('Location: ' . BASE_URL . 'cart/cart.php');
exit;