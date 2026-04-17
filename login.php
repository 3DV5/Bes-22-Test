<?php
session_start();
require_once 'conexao.php';

$erro = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['entrar'])) {
    $email = trim($_POST['email']);
    $senha = trim($_POST['senha']);

    if (!empty($email) && !empty($senha)) {
        $stmt = $pdo->prepare("SELECT id, nome, senha FROM usuarios WHERE email = ?");
        $stmt->execute([$email]);
        $usuario = $stmt->fetch();

        if ($usuario && password_verify($senha, $usuario['senha'])) {
            $_SESSION['usuario_id'] = $usuario['id'];
            $_SESSION['usuario_nome'] = $usuario['nome'];
            header('Location: tarefas.php');
            exit;
        } else {
            $erro = 'E-mail ou senha inválidos.';
        }
    } else {
        $erro = 'Preencha todos os campos.';
    }
}
?>
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <title>Login - Gerenciador de Tarefas</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
<div class="container">
    <h2>Acesso ao Sistema</h2>
    <?php if ($erro): ?>
        <div class="erro"><?= htmlspecialchars($erro) ?></div>
    <?php endif; ?>
    <form method="post">
        <label>E-mail</label>
        <input type="email" name="email" required>

        <label>Senha</label>
        <input type="password" name="senha" required>

        <button type="submit" name="entrar">Entrar</button>
    </form>
    <div class="links">
        <a href="recuperar_senha.php">Recuperar senha</a>
        <a href="novo_usuario.php">Novo usuário</a>
    </div>
</div>
</body>
</html>