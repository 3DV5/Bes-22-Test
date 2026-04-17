<?php
require_once 'conexao.php';
$mensagem = '';
$erro = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $nome = trim($_POST['nome']);
    $email = trim($_POST['email']);
    $senha = trim($_POST['senha']);
    $confirma = trim($_POST['confirma_senha']);

    if (empty($nome) || empty($email) || empty($senha)) {
        $erro = 'Todos os campos são obrigatórios.';
    } elseif ($senha !== $confirma) {
        $erro = 'As senhas não coincidem.';
    } else {
        // Verificar se e-mail já existe
        $stmt = $pdo->prepare("SELECT id FROM usuarios WHERE email = ?");
        $stmt->execute([$email]);
        if ($stmt->fetch()) {
            $erro = 'E-mail já cadastrado.';
        } else {
            $hash = password_hash($senha, PASSWORD_DEFAULT);
            $stmt = $pdo->prepare("INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)");
            if ($stmt->execute([$nome, $email, $hash])) {
                $mensagem = 'Cadastro realizado com sucesso! <a href="login.php">Faça login</a>';
            } else {
                $erro = 'Erro ao cadastrar. Tente novamente.';
            }
        }
    }
}
?>
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <title>Novo Usuário</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
<div class="container">
    <h2>Criar nova conta</h2>
    <?php if ($mensagem): ?>
        <div class="sucesso"><?= $mensagem ?></div>
    <?php elseif ($erro): ?>
        <div class="erro"><?= htmlspecialchars($erro) ?></div>
    <?php endif; ?>
    <form method="post">
        <label>Nome completo</label>
        <input type="text" name="nome" required>

        <label>E-mail</label>
        <input type="email" name="email" required>

        <label>Senha</label>
        <input type="password" name="senha" required>

        <label>Confirmar senha</label>
        <input type="password" name="confirma_senha" required>

        <button type="submit">Cadastrar</button>
    </form>
    <div class="links">
        <a href="login.php">Já tenho conta → faça login</a>
    </div>
</div>
</body>
</html>