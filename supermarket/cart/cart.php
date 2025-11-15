<?php include __DIR__ . '/../partials/header.php'; ?>
<?php if (empty($_SESSION['user_id'])) { header('Location: /auth/login.php'); exit; } ?>
<main class="container">
  <h1>Your Cart</h1>
  <?php
    $userId = (int)$_SESSION['user_id'];
    $stmt = $pdo->prepare('SELECT c.id as cart_id, c.quantity, p.id as product_id, p.name, p.price, p.image_url FROM cart c JOIN products p ON c.product_id = p.id WHERE c.user_id = ? ORDER BY p.name');
    $stmt->execute([$userId]);
    $items = $stmt->fetchAll();
    $total = 0.0;
  ?>
  <div class="cart-list">
    <?php foreach ($items as $it):
      $line = (float)$it['price'] * (int)$it['quantity'];
      $total += $line; ?>
      <div class="cart-row">
        <div class="thumb" style="background-image:url('<?php echo htmlspecialchars($it['image_url']); ?>')"></div>
        <div class="grow">
          <strong><?php echo htmlspecialchars($it['name']); ?></strong>
          <div class="muted">$<?php echo number_format((float)$it['price'],2); ?></div>
        </div>
        <form action="<?php echo BASE_URL; ?>cart/update.php" method="post" class="inline">
          <input type="hidden" name="cart_id" value="<?php echo (int)$it['cart_id']; ?>">
          <input type="number" name="quantity" value="<?php echo (int)$it['quantity']; ?>" min="1" class="qty">
          <button class="btn btn-outline" type="submit">Update</button>
        </form>
        <form action="<?php echo BASE_URL; ?>cart/remove.php" method="post" class="inline">
          <input type="hidden" name="cart_id" value="<?php echo (int)$it['cart_id']; ?>">
          <button class="btn btn-danger" type="submit">Remove</button>
        </form>
        <div class="line">$<?php echo number_format($line,2); ?></div>
      </div>
    <?php endforeach; ?>
    <?php if (!$items): ?>
      <p class="muted">Your cart is empty.</p>
    <?php endif; ?>
  </div>

  <div class="cart-summary">
    <div class="total">Total: $<?php echo number_format($total,2); ?></div>
    <a class="btn" href="<?php echo BASE_URL; ?>cart/checkout.php">Proceed to Checkout</a>
  </div>
</main>
<?php include __DIR__ . '/../partials/footer.php'; ?>