<?php include __DIR__ . '/../partials/header.php'; ?>
<?php
if (empty($_SESSION['user_id'])) { header('Location: /auth/login.php'); exit; }
$userStmt = $pdo->prepare('SELECT email FROM users WHERE id = ?');
$userStmt->execute([(int)$_SESSION['user_id']]);
$email = $userStmt->fetchColumn();
if (!$email || strtolower($email) !== 'admin@supermarket.local') { header('Location: /'); exit; }

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
        $stmt = $pdo->prepare('INSERT INTO products(name,category,description,price,stock,image_url) VALUES(?,?,?,?,?,?)');
        $stmt->execute([$name, $category, $description, $price, $stock, $image_url]);
        header('Location: ' . BASE_URL . 'admin/index.php');
        exit;
    }
}
?>
<main class="container">
  <h1>Add Product</h1>
  <?php if ($error) { echo '<div class="alert">' . htmlspecialchars($error) . '</div>'; } ?>
  <form method="post" class="form">
    <label>Name<input type="text" name="name" required></label>
    <label>Category<input type="text" name="category" required></label>
    <label>Description<textarea name="description"></textarea></label>
    <label>Price<input type="number" name="price" step="0.01" min="0" required></label>
    <label>Stock<input type="number" name="stock" min="0" required></label>
    <label>Image URL<input type="url" name="image_url"></label>
    <button class="btn" type="submit">Save</button>
  </form>
</main>
<?php include __DIR__ . '/../partials/footer.php'; ?>