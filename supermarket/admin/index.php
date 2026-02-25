<?php include __DIR__ . '/../partials/header.php'; ?>
<?php
if (empty($_SESSION['user_id'])) { header('Location: /auth/login.php'); exit; }
$userStmt = $pdo->prepare('SELECT email FROM users WHERE id = ?');
$userStmt->execute([(int)$_SESSION['user_id']]);
$email = $userStmt->fetchColumn();
if (!$email || strtolower($email) !== 'admin@supermarket.local') { header('Location: /'); exit; }
?>
<main class="container">
  <h1>Admin: Products</h1>
  <a class="btn" href="/admin/add_product.php">Add Product</a>
  <?php $stmt = $pdo->query('SELECT id, name, category, price, stock FROM products ORDER BY name'); ?>
  <table class="table">
    <thead><tr><th>Name</th><th>Category</th><th>Price</th><th>Stock</th><th>Actions</th></tr></thead>
    <tbody>
      <?php foreach ($stmt as $p): ?>
        <tr>
          <td><?php echo htmlspecialchars($p['name']); ?></td>
          <td><?php echo htmlspecialchars($p['category']); ?></td>
          <td>$<?php echo number_format((float)$p['price'],2); ?></td>
          <td><?php echo (int)$p['stock']; ?></td>
          <td>
            <a class="btn btn-outline" href="/admin/edit_product.php?id=<?php echo (int)$p['id']; ?>">Edit</a>
            <a class="btn btn-danger" href="/admin/delete_product.php?id=<?php echo (int)$p['id']; ?>" onclick="return confirm('Delete product?');">Delete</a>
          </td>
        </tr>
      <?php endforeach; ?>
    </tbody>
  </table>
</main>
<?php include __DIR__ . '/../partials/footer.php'; ?>