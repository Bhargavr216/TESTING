<?php include __DIR__ . '/../partials/header.php'; ?>
<?php if (empty($_SESSION['user_id'])) { header('Location: /auth/login.php'); exit; } ?>
<main class="container">
  <h1>Order History</h1>
  <?php
    $userId = (int)$_SESSION['user_id'];
    $orders = $pdo->prepare('SELECT id, total_amount, created_at FROM orders WHERE user_id = ? ORDER BY created_at DESC');
    $orders->execute([$userId]);
    $orders = $orders->fetchAll();
  ?>
  <?php if (!$orders): ?>
    <p class="muted">No orders yet.</p>
  <?php else: ?>
    <div class="orders">
      <?php foreach ($orders as $o): ?>
        <div class="order">
          <div>
            <strong>Order #<?php echo (int)$o['id']; ?></strong>
            <span class="muted"><?php echo htmlspecialchars($o['created_at']); ?></span>
          </div>
          <div>Total: $<?php echo number_format((float)$o['total_amount'], 2); ?></div>
          <?php
            $items = $pdo->prepare('SELECT oi.quantity, oi.price, p.name FROM order_items oi JOIN products p ON oi.product_id = p.id WHERE oi.order_id = ?');
            $items->execute([(int)$o['id']]);
          ?>
          <ul>
            <?php foreach ($items as $it): ?>
              <li><?php echo htmlspecialchars($it['name']); ?> × <?php echo (int)$it['quantity']; ?> — $<?php echo number_format((float)$it['price'] * (int)$it['quantity'], 2); ?></li>
            <?php endforeach; ?>
          </ul>
        </div>
      <?php endforeach; ?>
    </div>
  <?php endif; ?>
</main>
<?php include __DIR__ . '/../partials/footer.php'; ?>