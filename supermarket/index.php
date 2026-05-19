<?php include __DIR__ . '/partials/header.php'; ?>
<main>
  <section class="hero">
    <div class="container hero-inner">
      <div class="hero-text">
        <h1>Fresh, Fast, and Affordable</h1>
        <p>Your one-stop supermarket for daily essentials and delights.</p>
        <a class="btn" href="<?php echo BASE_URL; ?>products/index.php">Shop Now</a>
      </div>
      <div class="hero-art" aria-hidden="true"></div>
    </div>
  </section>

  <section class="offers">
    <div class="container">
      <h2>Weekly Offers</h2>
      <div class="grid">
        <div class="offer-card">10% off Fruits</div>
        <div class="offer-card">Buy 1 Get 1: Snacks</div>
        <div class="offer-card">Flat 15% on Beverages</div>
      </div>
    </div>
  </section>

  <section class="featured">
    <div class="container">
      <h2>Featured Products</h2>
      <div class="grid products">
        <?php
        $stmt = $pdo->query('SELECT id, name, category, price, stock, image_url FROM products ORDER BY id DESC LIMIT 8');
        foreach ($stmt as $p): ?>
          <div class="product-card">
            <div class="thumb" style="background-image:url('<?php echo htmlspecialchars($p['image_url']); ?>')"></div>
            <div class="info">
              <h3><?php echo htmlspecialchars($p['name']); ?></h3>
              <p class="muted"><?php echo htmlspecialchars($p['category']); ?></p>
              <p class="price">$<?php echo number_format((float)$p['price'], 2); ?></p>
              <form action="<?php echo BASE_URL; ?>cart/add.php" method="post" class="inline">
                <input type="hidden" name="product_id" value="<?php echo (int)$p['id']; ?>">
                <input type="number" name="quantity" value="1" min="1" class="qty">
                <button class="btn" type="submit">Add to Cart</button>
              </form>
            </div>
          </div>
        <?php endforeach; ?>
      </div>
    </div>
  </section>
</main>
<?php include __DIR__ . '/partials/footer.php'; ?>