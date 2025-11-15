<?php include __DIR__ . '/../partials/header.php'; ?>
<?php if (empty($_SESSION['user_id'])) { header('Location: ' . BASE_URL . 'auth/login.php'); exit; } ?>
<main class="container">
  <h1>Checkout</h1>
  <?php
    $userId = (int)$_SESSION['user_id'];
    $stmt = $pdo->prepare('SELECT c.id as cart_id, c.quantity, p.id as product_id, p.name, p.price FROM cart c JOIN products p ON c.product_id = p.id WHERE c.user_id = ?');
    $stmt->execute([$userId]);
    $items = $stmt->fetchAll();
    $total = 0.0;
    foreach ($items as $it) {
      $total += (float)$it['price'] * (int)$it['quantity'];
    }
  ?>
  <?php if (!$items): ?>
    <p class="muted">No items to checkout.</p>
  <?php else: ?>
    <div class="checkout-summary">
      <ul>
        <?php foreach ($items as $it): ?>
          <li><?php echo htmlspecialchars($it['name']); ?> × <?php echo (int)$it['quantity']; ?> — $<?php echo number_format((float)$it['price'] * (int)$it['quantity'], 2); ?></li>
        <?php endforeach; ?>
      </ul>
      <div class="total">Total: $<?php echo number_format($total, 2); ?></div>
    </div>
    <form action="<?php echo BASE_URL; ?>cart/place_order.php" method="post" class="form">
      <button class="btn" type="submit">Place Order</button>
    </form>
  <?php endif; ?>
</main>
<?php include __DIR__ . '/../partials/footer.php'; ?>