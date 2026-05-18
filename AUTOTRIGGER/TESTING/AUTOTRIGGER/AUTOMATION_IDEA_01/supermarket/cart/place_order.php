<?php
include __DIR__ . '/../config/db.php';
if (session_status() === PHP_SESSION_NONE) { session_start(); }
if (empty($_SESSION['user_id'])) { header('Location: ' . BASE_URL . 'auth/login.php'); exit; }

$userId = (int)$_SESSION['user_id'];
$pdo->beginTransaction();

$cartStmt = $pdo->prepare('SELECT c.id, c.quantity, p.id as product_id, p.price, p.stock FROM cart c JOIN products p ON c.product_id = p.id WHERE c.user_id = ? FOR UPDATE');
$cartStmt->execute([$userId]);
$items = $cartStmt->fetchAll();
if (!$items) {
    $pdo->rollBack();
    header('Location: ' . BASE_URL . 'cart/cart.php');
    exit;
}

$total = 0.0;
foreach ($items as $it) {
    if ((int)$it['stock'] < (int)$it['quantity']) {
        $pdo->rollBack();
        header('Location: ' . BASE_URL . 'cart/cart.php');
        exit;
    }
    $total += (float)$it['price'] * (int)$it['quantity'];
}

$orderIns = $pdo->prepare('INSERT INTO orders(user_id, total_amount, created_at) VALUES(?,?,NOW())');
$orderIns->execute([$userId, $total]);
$orderId = (int)$pdo->lastInsertId();

$itemIns = $pdo->prepare('INSERT INTO order_items(order_id, product_id, quantity, price) VALUES(?,?,?,?)');
$stockUpd = $pdo->prepare('UPDATE products SET stock = stock - ? WHERE id = ?');
$cartDel = $pdo->prepare('DELETE FROM cart WHERE id = ?');

foreach ($items as $it) {
    $itemIns->execute([$orderId, (int)$it['product_id'], (int)$it['quantity'], (float)$it['price']]);
    $stockUpd->execute([(int)$it['quantity'], (int)$it['product_id']]);
    $cartDel->execute([(int)$it['id']]);
}

$pdo->commit();
header('Location: ' . BASE_URL . 'orders/history.php');
exit;