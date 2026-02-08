<?php include __DIR__ . '/../partials/header.php'; ?>
<?php
if (empty($_SESSION['user_id'])) { header('Location: /auth/login.php'); exit; }
$userStmt = $pdo->prepare('SELECT email FROM users WHERE id = ?');
$userStmt->execute([(int)$_SESSION['user_id']]);
$email = $userStmt->fetchColumn();
if (!$email || strtolower($email) !== 'admin@supermarket.local') { header('Location: /'); exit; }

$id = isset($_GET['id']) ? (int)$_GET['id'] : 0;
if ($id <= 0) { header('Location: /admin/index.php'); exit; }
$p = $pdo->prepare('SELECT * FROM products WHERE id = ?');
$p->execute([$id]);
$product = $p->fetch();
if (!$product) { header('Location: /admin/index.php'); exit; }

$error = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $name = trim($_POST['name'] ?? '');
    $category = trim($_POST['category'] ?? '');
    $description = trim($_POST['description'] ?? '');
    $price = isset($_POST['price']) ? (float)$_POST['price'] : 0;
    $stock = isset($_POST['stock']) ? (int)$_POST['stock'] : 0;
    $image_url = trim($_POST['image_url'] ?? '');
    if ($name === '' || $category === '' || $price <= 0) {
        $error = 'Name, category, and positive price required';
    } else {
        $stmt = $pdo->prepare('UPDATE products SET name=?, category=?, description=?, price=?, stock=?, image_url=? WHERE id=?');
        $stmt->execute([$name, $category, $description, $price, $stock, $image_url, $id]);
        header('Location: ' . BASE_URL . 'admin/index.php');
        exit;
    }
}
?>
<main class="container">
  <h1>Edit Product</h1>
  <?php if ($error) { echo '<div class="alert">' . htmlspecialchars($error) . '</div>'; } ?>
  <form method="post" class="form">
    <label>Name<input type="text" name="name" value="<?php echo htmlspecialchars($product['name']); ?>" required></label>
    <label>Category<input type="text" name="category" value="<?php echo htmlspecialchars($product['category']); ?>" required></label>
    <label>Description<textarea name="description"><?php echo htmlspecialchars($product['description']); ?></textarea></label>
    <label>Price<input type="number" name="price" step="0.01" min="0" value="<?php echo htmlspecialchars($product['price']); ?>" required></label>
    <label>Stock<input type="number" name="stock" min="0" value="<?php echo htmlspecialchars($product['stock']); ?>" required></label>
    <label>Image URL<input type="url" name="image_url" value="<?php echo htmlspecialchars($product['image_url']); ?>"></label>
    <button class="btn" type="submit">Update</button>
  </form>
</main>
<?php include __DIR__ . '/../partials/footer.php'; ?>