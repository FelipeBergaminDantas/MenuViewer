# Melhoria: painel admin do restaurante

Este documento resume a melhoria feita no projeto: o que motivou, o que foi implementado, os problemas encontrados no caminho e como tudo foi verificado. O guia de uso do painel está em [docs/PAINEL_ADMIN.md](docs/PAINEL_ADMIN.md).

## 1. Situação antes da melhoria

O projeto já tinha uma base sólida: código organizado, acessibilidade bem cuidada, tradução para pt/en/es, filtros de alergia rodando no banco e 87 testes passando.

O maior problema era outro: **o restaurante não tinha como alterar o próprio cardápio.** Os pratos só existiam no arquivo `app/seed.py`, então qualquer mudança de preço, prato novo ou ingrediente exigia editar código. Esse item já constava no README como a primeira das "Ideias para o futuro".

## 2. O que foi feito

Foi criado um painel em `/admin`, protegido por login, onde a equipe pode:

- **Pratos:** criar, editar e excluir; marcar como indisponível (sai do cardápio sem ser apagado); escolher categoria, ingredientes, foto e ordem.
- **Categorias:** criar, editar e excluir (só quando não têm pratos).
- **Ingredientes:** criar, editar e excluir, informando a origem (vegetal, derivado animal ou carne) e os alérgenos.

Para criar o primeiro acesso, há um comando novo:

```bash
flask --app run db upgrade
flask --app run criar-admin equipe     # pede a senha (mínimo 8 caracteres)
```

### Princípios mantidos do projeto

| Princípio do projeto | Como o painel segue |
|---|---|
| Alérgenos vêm dos ingredientes | O prato não tem campo "sem glúten". Ao editar um ingrediente, todos os pratos que o usam são atualizados, e a tela avisa quais são |
| Funcionar sem JavaScript | Só formulários HTML comuns; excluir passa por uma página de confirmação |
| Acessibilidade em primeiro lugar | Resumo de erros com links para os campos, `aria-invalid` e `aria-describedby`, foco levado à mensagem, foto obrigatoriamente com texto alternativo |
| Nenhum texto fixo nos templates | Todos os textos do painel estão em `pt.json`, `en.json` e `es.json` |
| Sem dependências pesadas | Nenhuma biblioteca nova; usa a sessão do Flask e o `werkzeug`, que já vem com ele |

### Segurança

- Senhas guardadas com hash, nunca em texto puro.
- A sessão é recriada a cada login, o que impede reaproveitar uma sessão antiga.
- Todo formulário do admin leva um token CSRF. Um envio sem o token é recusado com erro 400.
- O redirecionamento após o login só aceita endereços do próprio site.
- As páginas do admin não ficam em cache, então não reaparecem pelo botão "voltar" depois de sair.

## 3. Problemas encontrados e corrigidos no caminho

1. **Excluir ingrediente deixaria dados órfãos.** O SQLite ignora `ON DELETE CASCADE` por padrão, então a ligação entre prato e ingrediente continuaria no banco. Se um ingrediente novo reaproveitasse o mesmo id, ele "entraria" em pratos antigos, levando seus alérgenos junto, o que é grave num cardápio para alérgicos. A correção foi criar a relação inversa `Ingrediente.pratos`, para que o próprio SQLAlchemy apague essas ligações.
2. **O app subia em produção com a chave secreta de desenvolvimento.** Com o login, isso passou a ser crítico: quem conhece a chave consegue forjar a sessão e entrar no painel. Agora o app se recusa a iniciar em produção sem a variável `SECRET_KEY`, e o CI define uma chave própria.

## 4. Arquivos

**Novos**

| Arquivo | Conteúdo |
|---|---|
| `app/routes/admin.py` | Rotas do painel (login exigido em todas) |
| `app/seguranca.py` | Login, sessão, CSRF e validação de redirecionamento |
| `app/services/admin.py` | Validação dos formulários |
| `app/templates/admin/` | 10 templates: layout, login, listas, formulários, confirmação de exclusão e macros |
| `migrations/versions/36f903ed20ef_usuarios_do_painel_admin.py` | Tabela `usuarios` |
| `tests/test_admin.py` | 18 testes do painel |
| `docs/PAINEL_ADMIN.md` | Guia de uso do painel |

**Alterados**

| Arquivo | Mudança |
|---|---|
| `app/models.py` | Modelo `Usuario` e relação `Ingrediente.pratos` |
| `app/__init__.py` | Comando `criar-admin`, registro do painel, exigência de `SECRET_KEY` em produção |
| `app/config.py` | Configuração do cookie de sessão |
| `app/routes/preferencias.py` | Passa a usar a validação de redirecionamento de `seguranca.py` |
| `app/templates/base.html` | Link "Área da equipe" no rodapé |
| `app/static/css/style.css` | Estilos do painel, incluindo o modo de alto contraste |
| `app/translations/*.json` | Textos do painel nos três idiomas (só acréscimos) |
| `.github/workflows/ci.yml` | `SECRET_KEY` para o passo de migrations |

## 5. Verificação

| Verificação | Resultado |
|---|---|
| `pytest` | **105 testes passando** (eram 87; 18 novos) |
| `npm test` | 23 testes passando (sem alteração) |
| Migration | Sobe, desce e sobe de novo; `flask db check` confirma que bate com os modelos |
| Telas do painel | Todas carregam nos três idiomas, sem texto de tradução faltando |
| Contraste da cor de erro | 6,5:1 no tema padrão e 9,2:1 no alto contraste (WCAG AA exige 4,5:1) |

Os novos testes cobrem: login e logout, bloqueio sem login, CSRF, redirecionamento seguro, criação/edição/exclusão das três entidades, mensagens de erro acessíveis, prato indisponível sumindo do cardápio, alérgeno de ingrediente mudando o filtro dos pratos, ausência de dados órfãos, o comando `criar-admin` e a exigência de `SECRET_KEY`.

## 6. O que ficou de fora

- **Upload de fotos:** por enquanto o painel só permite escolher arquivos que já estão em `app/static/img/pratos`.
- **Limite de tentativas de login:** recomenda-se configurar no servidor ou com Flask-Limiter.
- **Níveis de permissão:** todos os usuários do painel têm o mesmo acesso.
- **Edição de alérgenos:** a lista é fixa (base Anvisa) e não muda pelo painel.
