<?php
if (!isset($pdo)) {
    require_once __DIR__ . '/../config/db.php';
}

$user = null;
if (!empty($_SESSION['user_id'])) {
    $stmt = $pdo->prepare('SELECT id, name, email FROM users WHERE id = ?');
    $stmt->execute([$_SESSION['user_id']]);
    $user = $stmt->fetch();
}

$isAdmin = $user && strtolower($user['email']) === 'admin@supermarket.local';
?>
<header class="site-header">
  <div class="container nav">
    <a class="brand" href="<?php echo BASE_URL; ?>">Supermarket</a>
    <nav class="menu">
      <a href="<?php echo BASE_URL; ?>">Home</a>
      <a href="<?php echo BASE_URL; ?>products/index.php">Products</a>
      <a href="<?php echo BASE_URL; ?>cart/cart.php">Cart</a>
      <?php if ($user): ?>
        <a href="<?php echo BASE_URL; ?>orders/history.php">Orders</a>
        <?php if ($isAdmin): ?><a href="<?php echo BASE_URL; ?>admin/index.php">Admin</a><?php endif; ?>
        <span class="user">Hello, <?php echo htmlspecialchars($user['name']); ?></span>
        <a class="btn btn-outline" href="<?php echo BASE_URL; ?>auth/logout.php">Logout</a>
      <?php else: ?>
        <a href="<?php echo BASE_URL; ?>auth/login.php">Login</a>
        <a class="btn" href="<?php echo BASE_URL; ?>auth/register.php">Sign Up</a>
      <?php endif; ?>
    </nav>
  </div>
</header>