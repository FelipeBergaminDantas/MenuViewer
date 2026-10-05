# Painel admin

Área em `/admin` onde a equipe do restaurante cadastra **pratos**, **categorias** e **ingredientes** sem mexer no código. Antes dela, o cardápio só podia ser alterado editando `app/seed.py`.

## Como usar

```bash
flask --app run db upgrade                 # cria a tabela de usuários (nova migration)
flask --app run criar-admin equipe         # pede a senha (mínimo 8 caracteres)
python run.py
```

Acesse `http://127.0.0.1:5000/admin` (também há o link **"Área da equipe"** no rodapé). Rodar `criar-admin` com um usuário que já existe troca a senha dele.

> Em produção (`FLASK_CONFIG=production`) o app **não sobe** sem a variável `SECRET_KEY`. Quem conhece a chave consegue forjar a sessão e entrar no painel.

## O que dá para fazer

| Seção | Ações |
|---|---|
| **Pratos** | Criar, editar e excluir. Campos: nome, descrição, preço (`24,90` ou `24.90`), categoria, ingredientes, picante, disponível, foto + descrição da foto, ordem |
| **Categorias** | Criar, editar e excluir. Uma categoria **com pratos não pode ser excluída** |
| **Ingredientes** | Criar, editar e excluir. Campos: nome (único), origem (vegetal / derivado animal / carne) e alérgenos |

- **Desmarcar "Disponível"** tira o prato do cardápio sem apagá-lo (para quando ele está em falta).
- **Alérgenos e dietas continuam sendo calculados a partir dos ingredientes.** Por exemplo, marcar "glúten" no tomate esconde a bruschetta no filtro "sem glúten". Por isso a tela de edição de um ingrediente avisa quais pratos serão afetados.
- **Excluir sempre passa por uma tela de confirmação.** Ao excluir um ingrediente, a confirmação mostra os pratos que o usam.

## Decisões de implementação

**Segurança (sem dependências novas)**
- Login com senha salva com hash (`werkzeug.security`) e sessão assinada do Flask. A sessão é recriada a cada login, o que evita reaproveitar uma sessão antiga (*session fixation*).
- **CSRF:** todo `POST` em `/admin` precisa de um token aleatório guardado na sessão. Sem ele, a resposta é `400`.
- O parâmetro `next` do login só aceita caminhos do próprio site, o que evita redirecionar para outro site (*open redirect*).
- As páginas do admin vão com `Cache-Control: no-store`, para não aparecerem pelo botão "voltar" depois de sair.

**Acessibilidade**, seguindo o mesmo padrão do cardápio:
- Tudo funciona sem JavaScript: formulários comuns e exclusão por página de confirmação.
- Quando há erros, um resumo no topo recebe o foco e tem links para cada campo. Os campos com erro levam `aria-invalid` e `aria-describedby`, e o que a pessoa digitou não se perde.
- **Foto exige texto alternativo:** não dá para salvar um prato com foto sem a descrição dela.
- O painel de acessibilidade (fonte, contraste, idioma) também vale no admin, e todos os textos estão em pt, en e es.

**Integridade dos dados**
- Foi criada a relação inversa `Ingrediente.pratos`. Sem ela, excluir um ingrediente deixaria linhas órfãs em `prato_ingrediente`, porque o SQLite ignora `ON DELETE CASCADE` por padrão. Um ingrediente novo que reaproveitasse o mesmo id "entraria" em pratos antigos, levando os alérgenos junto.

## Arquivos

| Arquivo | O que faz |
|---|---|
| `app/routes/admin.py` | Rotas do painel; o login é exigido em `before_request` |
| `app/seguranca.py` | Login, sessão, CSRF e `destino_seguro` (movido de `routes/preferencias.py`) |
| `app/services/admin.py` | Validação dos formulários: devolve `(dados, erros)` |
| `app/models.py` | Modelo `Usuario` e relação `Ingrediente.pratos` |
| `app/templates/admin/` | Telas do painel e macros de formulário (`_form.html`) |
| `app/__init__.py`, `app/config.py` | Comando `criar-admin`, cookie de sessão e exigência da `SECRET_KEY` em produção |
| `migrations/versions/36f903ed20ef_*.py` | Tabela `usuarios` |
| `tests/test_admin.py` | 18 testes: login, CSRF, CRUD, validação, alérgenos derivados, CLI |

Também mudaram as traduções (`app/translations/*.json`), o CSS (seção "Painel admin") e o CI, que agora define uma `SECRET_KEY`.

## Limitações e próximos passos

- **Fotos:** o painel só deixa escolher arquivos que já estão em `app/static/img/pratos`. Ainda não há upload.
- **Login:** não há limite de tentativas. Em produção, convém limitar no proxy reverso ou usar uma extensão como Flask-Limiter.
- Todos os usuários têm o mesmo acesso; não há níveis de permissão.
- Os alérgenos são fixos (a lista da Anvisa no `seed.py`) e não podem ser editados pelo painel.
