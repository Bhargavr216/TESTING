<?php include __DIR__ . '/../partials/header.php'; ?>
<main class="container">
  <h1>Products</h1>
  <form class="filters" method="get">
    <input type="text" name="q" placeholder="Search products" value="<?php echo isset($_GET['q'])? htmlspecialchars($_GET['q']) : ''; ?>" />
    <select name="category">
      <option value="">All Categories</option>
      <?php
        $catsStmt = $pdo->query("SELECT DISTINCT category FROM products ORDER BY category ASC");
        $selected = isset($_GET['category']) ? $_GET['category'] : '';
        foreach ($catsStmt as $row) {
          $cat = $row['category'];
          $isSel = $selected === $cat ? 'selected' : '';
          echo "<option value='" . htmlspecialchars($cat) . "' $isSel>" . htmlspecialchars($cat) . "</option>";
        }
      ?>
    </select>
    <button class="btn" type="submit">Filter</button>
  </form>

  <div class="grid products">
    <?php
      $q = isset($_GET['q']) ? trim($_GET['q']) : '';
      $category = isset($_GET['category']) ? trim($_GET['category']) : '';

      $sql = 'SELECT id, name, category, description, price, stock, image_url FROM products WHERE 1=1';
      $params = [];
      if ($q !== '') {
        $sql .= ' AND name LIKE ?';
        $params[] = '%' . $q . '%';
      }
      if ($category !== '') {
        $sql .= ' AND category = ?';
        $params[] = $category;
      }
      $sql .= ' ORDER BY name ASC';
      $stmt = $pdo->prepare($sql);
      $stmt->execute($params);

      foreach ($stmt as $p): ?>
        <div class="product-card">
          <div class="thumb" style="background-image:url('<?php echo htmlspecialchars($p['image_url']); ?>')"></div>
          <div class="info">
            <h3><?php echo htmlspecialchars($p['name']); ?></h3>
            <p class="muted"><?php echo htmlspecialchars($p['category']); ?></p>
            <p><?php echo htmlspecialchars($p['description']); ?></p>
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
</main>
<?php include __DIR__ . '/../partials/footer.php'; ?>