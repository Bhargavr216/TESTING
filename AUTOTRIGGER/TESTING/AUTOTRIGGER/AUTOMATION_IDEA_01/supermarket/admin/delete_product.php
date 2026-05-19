<?php
include __DIR__ . '/../config/db.php';
if (session_status() === PHP_SESSION_NONE) { session_start(); }
if (empty($_SESSION['user_id'])) { header('Location: /auth/login.php'); exit; }
$userStmt = $pdo->prepare('SELECT email FROM users WHERE id = ?');
$userStmt->execute([(int)$_SESSION['user_id']]);
$email = $userStmt->fetchColumn();
if (!$email || strtolower($email) !== 'admin@supermarket.local') { header('Location: /'); exit; }

$id = isset($_GET['id']) ? (int)$_GET['id'] : 0;
if ($id > 0) {
    $stmt = $pdo->prepare('DELETE FROM products WHERE id = ?');
    $stmt->execute([$id]);
}
header('Location: ' . BASE_URL . 'admin/index.php');
exit;