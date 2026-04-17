<?php
require_once 'conexao.php';
$mensagem = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email = trim($_POST['email']);

    if (!empty($email)) {
        // Verificar se e-mail existe
        $stmt = $pdo->prepare("SELECT id FROM usuarios WHERE email = ?");
        $stmt->execute([$email]);
        $usuario = $stmt->fetch();

        if ($usuario) {
            $token = bin2hex(random_bytes(32));
            $expira = date('Y-m-d H:i:s', strtotime('+1 hour'));

            // Remove tokens antigos para este usuário (opcional)
            $stmt = $pdo->prepare("DELETE FROM recuperacao_senha WHERE usuario_id = ?");
            $stmt->execute([$usuario['id']]);

            // Insere novo token
            $stmt = $pdo->prepare("INSERT INTO recuperacao_senha (usuario_id, token, expira_em) VALUES (?, ?, ?)");
            $stmt->execute([$usuario['id'], $token, $expira]);

            // Em um sistema real, enviaria e-mail com link contendo o token
            // Exemplo de link: http://seusite.com/redefinir_senha.php?token=$token
            $mensagem = "Link de recuperação (simulado): <br> <code>redefinir_senha.php?token=$token</code> <br>
                         Esse token expira em 1 hora. (Funcionalidade a ser implementada no módulo de redefinição)";
        } else {
            $mensagem = 'Se o e-mail existir, você receberá as instruções. (Simulação)';
        }
    } else {
        $mensagem = 'Informe seu e-mail.';
    }
}
?>
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <title>Recuperar Senha</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
<div class="container">
    <h2>Recuperar Senha</h2>
    <?php if ($mensagem): ?>
        <div class="sucesso"><?= $mensagem ?></div>
    <?php endif; ?>
    <form method="post">
        <label>E-mail cadastrado</label>
        <input type="email" name="email" required>
        <button type="submit">Enviar link</button>
    </form>
    <div class="links">
        <a href="login.php">Voltar para o login</a>
    </div>
</div>
</body>
</html>