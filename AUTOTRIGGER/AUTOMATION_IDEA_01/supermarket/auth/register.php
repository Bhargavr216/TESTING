<?php include __DIR__ . '/../partials/header.php'; ?>
<main class="container auth">
  <h1>Create Account</h1>
  <?php
  $error = '';
  if ($_SERVER['REQUEST_METHOD'] === 'POST') {
      $name = trim($_POST['name'] ?? '');
      $email = trim($_POST['email'] ?? '');
      $password = $_POST['password'] ?? '';

      if ($name === '' || strlen($name) < 2) {
          $error = 'Name is required';
      } elseif (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
          $error = 'Valid email required';
      } elseif (strlen($password) < 6) {
          $error = 'Password must be at least 6 characters';
      } else {
          $exists = $pdo->prepare('SELECT id FROM users WHERE email = ?');
          $exists->execute([$email]);
          if ($exists->fetch()) {
              $error = 'Email already registered';
          } else {
              $hash = password_hash($password, PASSWORD_DEFAULT);
              $stmt = $pdo->prepare('INSERT INTO users(name,email,password) VALUES(?,?,?)');
              $stmt->execute([$name, $email, $hash]);
              $_SESSION['user_id'] = (int)$pdo->lastInsertId();
              header('Location: ' . BASE_URL);
              exit;
          }
      }
  }
  if ($error) {
      echo '<div class="alert">' . htmlspecialchars($error) . '</div>';
  }
  ?>
  <form method="post" class="form">
    <label>Name<input type="text" name="name" required></label>
    <label>Email<input type="email" name="email" required></label>
    <label>Password<input type="password" name="password" minlength="6" required></label>
    <button class="btn" type="submit">Sign Up</button>
    <p class="muted">Already have an account? <a href="<?php echo BASE_URL; ?>auth/login.php">Login</a></p>
  </form>
</main>
<?php include __DIR__ . '/../partials/footer.php'; ?>