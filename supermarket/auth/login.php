<?php include __DIR__ . '/../partials/header.php'; ?>
<main class="container auth">
  <h1>Login</h1>
  <?php
  $error = '';
  if ($_SERVER['REQUEST_METHOD'] === 'POST') {
      $email = trim($_POST['email'] ?? '');
      $password = $_POST['password'] ?? '';
      if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
          $error = 'Valid email required';
      } else {
          $stmt = $pdo->prepare('SELECT id, name, email, password FROM users WHERE email = ?');
          $stmt->execute([$email]);
          $user = $stmt->fetch();
          if (!$user || !password_verify($password, $user['password'])) {
              $error = 'Invalid credentials';
          } else {
              $_SESSION['user_id'] = (int)$user['id'];
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
    <label>Email<input type="email" name="email" required></label>
    <label>Password<input type="password" name="password" minlength="6" required></label>
    <button class="btn" type="submit">Login</button>
    <p class="muted">No account? <a href="<?php echo BASE_URL; ?>auth/register.php">Sign up</a></p>
  </form>
</main>
<?php include __DIR__ . '/../partials/footer.php'; ?>