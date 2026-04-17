# Task Manager — Software-Base da Disciplina de Testes

Aplicação web de **gerenciamento de tarefas** utilizada como software-base ao longo da disciplina de Testes de Software. Serve de base para aplicação progressiva de técnicas de teste de unidade, integração, sistema e aceitação.

---

## Funcionalidades

| Tela | Descrição |
|------|-----------|
| **Login** | Autenticação com e-mail/senha e recuperação de senha |
| **Painel** | Lista de tarefas com filtros por status, prioridade e responsável, ordenação e atualização rápida de status |
| **Nova / Editar Tarefa** | Formulário com validação completa (campos obrigatórios, formato de prazo DD/MM/AAAA, data futura) |
| **Relatórios** | Visualização por período, responsável e prioridade; exportação em **CSV** e **PDF** |

### Regras de negócio
- **Campos obrigatórios:** Título (máx. 100 chars), Prazo (DD/MM/AAAA, data atual ou futura), Responsável
- **Descrição:** opcional, máx. 500 chars
- **Status:** `pendente` → `em andamento` → `concluída`
- **Prioridade:** `baixa`, `média`, `alta`
- **Perfis:** `aluno`, `professor`, `admin` — somente professor e admin podem excluir tarefas

---

## Tecnologias

- **Backend:** Python 3.10+ · Flask · Flask-Login · Flask-SQLAlchemy · SQLite
- **Frontend:** Bootstrap 5 · Bootstrap Icons
- **Relatórios:** reportlab (PDF) · csv stdlib (CSV)
- **Testes:** pytest · pytest-flask

---

## Instalação e execução

```bash
# 1. Clone o repositório e entre na pasta
git clone https://github.com/Pacheco-15/Bes-22-Test.git
cd Bes-22-Test

# 2. Crie e ative um ambiente virtual
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Inicialize o banco e carregue dados de exemplo
flask init-db
flask seed-db

# 5. Execute a aplicação
flask run
```

Acesse em `http://127.0.0.1:5000`

### Usuários de exemplo (após seed-db)

| E-mail | Senha | Perfil |
|--------|-------|--------|
| admin@test.com | admin123 | admin |
| professor@test.com | prof123 | professor |
| aluno@test.com | aluno123 | aluno |

---

## Testes

```bash
pytest -v
```

### Estrutura de testes

| Arquivo | Tipo | O que cobre |
|---------|------|-------------|
| `tests/test_models.py` | **Unidade** | Modelos `User` e `Task` (hash de senha, labels, `is_overdue`) |
| `tests/test_validations.py` | **Unidade** | Todas as regras de validação do formulário de tarefa e e-mail |
| `tests/test_routes.py` | **Integração** | Fluxo completo: login, CRUD de tarefas, permissões, relatórios e exportação |

---

## Algoritmo: Fluxo de Criação e Validação de Tarefa

1. Usuário acessa "Nova Tarefa"
2. Sistema exibe formulário com campos: título, descrição, prazo, prioridade e responsável
3. Usuário preenche os campos e aciona "Criar tarefa"
4. Sistema verifica se todos os campos obrigatórios estão preenchidos
5. Sistema valida o formato do prazo (data atual ou futura, formato DD/MM/AAAA)
6. **Se inválido:** exibe mensagem de erro e retorna ao formulário
7. **Se válido:** persiste a tarefa e exibe confirmação ao usuário
8. Sistema atualiza o painel de tarefas com o novo item
