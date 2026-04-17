<?php
session_start();
if (!isset($_SESSION['usuario_id'])) {
    header('Location: login.php');
    exit;
}

require_once 'conexao.php';
$usuario_id = $_SESSION['usuario_id'];

// Adicionar tarefa
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['adicionar'])) {
    $descricao = trim($_POST['descricao']);
    if (!empty($descricao)) {
        $stmt = $pdo->prepare("INSERT INTO tarefas (usuario_id, descricao) VALUES (?, ?)");
        $stmt->execute([$usuario_id, htmlspecialchars($descricao)]);
    }
    header('Location: tarefas.php');
    exit;
}

// Concluir tarefa
if (isset($_GET['concluir'])) {
    $id = $_GET['concluir'];
    $stmt = $pdo->prepare("UPDATE tarefas SET status = 1 WHERE id = ? AND usuario_id = ?");
    $stmt->execute([$id, $usuario_id]);
    header('Location: tarefas.php');
    exit;
}

// Excluir tarefa
if (isset($_GET['excluir'])) {
    $id = $_GET['excluir'];
    $stmt = $pdo->prepare("DELETE FROM tarefas WHERE id = ? AND usuario_id = ?");
    $stmt->execute([$id, $usuario_id]);
    header('Location: tarefas.php');
    exit;
}

// Buscar tarefas do usuário
$stmt = $pdo->prepare("SELECT * FROM tarefas WHERE usuario_id = ? ORDER BY created_at DESC");
$stmt->execute([$usuario_id]);
$tarefas = $stmt->fetchAll();
?>
<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <title>Minhas Tarefas</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
<div class="container">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <h2>Bem-vindo, <?= htmlspecialchars($_SESSION['usuario_nome']) ?>!</h2>
        <a href="logout.php" class="logout">Sair</a>
    </div>

    <form method="post" class="form-add">
        <input type="text" name="descricao" placeholder="Digite uma nova tarefa..." required>
        <button type="submit" name="adicionar">Adicionar</button>
    </form>

    <h3>Lista de tarefas</h3>
    <?php if (empty($tarefas)): ?>
        <p style="color:#666;">Nenhuma tarefa cadastrada. Adicione uma acima.</p>
    <?php else: ?>
        <ul class="lista-tarefas">
            <?php foreach ($tarefas as $tarefa): ?>
                <li class="<?= $tarefa['status'] ? 'concluida' : '' ?>">
                    <span><?= htmlspecialchars($tarefa['descricao']) ?></span>
                    <div>
                        <?php if (!$tarefa['status']): ?>
                            <a href="?concluir=<?= $tarefa['id'] ?>" class="btn-concluir">✔ Concluir</a>
                        <?php else: ?>
                            <span class="badge-concluida">✓ Finalizada</span>
                        <?php endif; ?>
                        <a href="?excluir=<?= $tarefa['id'] ?>" class="btn-excluir" onclick="return confirm('Excluir tarefa?')">🗑 Excluir</a>
                    </div>
                </li>
            <?php endforeach; ?>
        </ul>
    <?php endif; ?>
</div>
</body>
</html>