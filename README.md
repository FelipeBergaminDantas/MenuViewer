<img width="2752" height="1536" alt="Gemini_Generated_Image_jt1scljt1scljt1s" src="https://github.com/user-attachments/assets/d35ca042-1c81-4b05-9664-2618044e5cf5" />


# 🍽️ Cardápio Acessível

Um cardápio digital para restaurantes com foco em **acessibilidade**, feito para ser simples, leve e fácil de estender via colaborações no GitHub.

## Funcionalidades

- **Painel de acessibilidade** (um só lugar para todas as opções)
  - Tamanho do texto de 80% a 200%, com o valor atual exibido
  - Alto contraste, reduzir movimento (também respeita a preferência do sistema)
  - **Modo simplificado**: uma categoria por vez, botões grandes, menos elementos na tela
  - Idioma da interface: português, inglês e espanhol (detecta o idioma do navegador)
  - As escolhas ficam salvas em cookie e a página já carrega no estado certo
- **Filtros alimentares e de alergias**: vegano, vegetariano, sem pimenta e exclusão dos principais alérgenos (glúten, leite, ovo, soja, amendoim, castanhas, peixe, crustáceos, gergelim)
- **Comandos de voz** para navegar sem toque ou clique: “próximo prato”, “voltar”, “ler descrição”, “mostrar ingredientes”, o nome de um prato…
- **QR Code do cardápio** para imprimir e colocar nas mesas (`/qrcode`, em SVG ou PNG)
- **Teclado e leitores de tela**: HTML semântico, ordem de foco lógica, foco sempre visível, link "pular para o cardápio", pratos anunciados como uma unidade (nome, preço, descrição)
- **Funciona sem JavaScript**: filtros, preferências e modo simplificado são formulários e links comuns; o JS só melhora a experiência (exceto os comandos de voz, que dependem do navegador)

## Stack

- **Backend**: Flask + Flask-SQLAlchemy + Flask-Migrate (Alembic)
- **Banco**: SQLite por padrão (qualquer banco suportado pelo SQLAlchemy via `DATABASE_URL`)
- **Frontend**: Jinja2 + HTML semântico + CSS + JavaScript vanilla em módulos ES (sem frameworks, sem build)
- **QR Code**: [segno](https://github.com/heuer/segno) (Python puro, sem dependências)

## Como rodar

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Acesse `http://127.0.0.1:5000`. Na primeira execução o banco é criado em `instance/menu.db` (via migrations) e populado com pratos de exemplo.

### Configuração (variáveis de ambiente)

| Variável | Padrão | Para quê |
|---|---|---|
| `FLASK_CONFIG` | `development` | `development`, `testing` ou `production` |
| `SECRET_KEY` | valor de dev | **Obrigatório trocar em produção** |
| `DATABASE_URL` | SQLite em `instance/` | ex.: `postgresql://usuario:senha@host/cardapio` |
| `PUBLIC_BASE_URL` | URL da requisição | Endereço público usado no QR Code, ex.: `https://cardapio.meurestaurante.com.br` |

### Banco de dados

```bash
flask --app run db upgrade          # aplica as migrations
flask --app run seed                # insere os dados de exemplo (só se o banco estiver vazio)
flask --app run db migrate -m "..." # gera uma migration após alterar app/models.py
```

## Testes

```bash
pip install -r requirements-dev.txt
pytest                # backend, filtros, modo simplificado, preferências, acessibilidade, QR Code
npm test              # interpretador dos comandos de voz (Node 22+, sem dependências)
```

## Estrutura do projeto

```
app/
├── __init__.py              # application factory, contexto dos templates, comandos CLI
├── config.py                # configurações por ambiente
├── extensions.py            # instâncias de SQLAlchemy e Migrate
├── models.py                # Categoria, Prato, Ingrediente, Alergeno
├── seed.py                  # dados de exemplo
├── i18n.py                  # traduções da interface (feitas no servidor)
├── preferences.py           # preferências de acessibilidade (cookie)
├── formatting.py            # formatação de preço por idioma
├── services/cardapio.py     # filtros alimentares/alergias (consultas SQL)
├── routes/
│   ├── menu.py              # cardápio completo e modo simplificado
│   ├── preferencias.py      # POST /preferencias (formulário ou fetch)
│   └── qrcode.py            # /qrcode, /qrcode.svg, /qrcode.png
├── templates/
│   ├── base.html, menu.html, menu_simplificado.html, qrcode.html
│   └── partials/            # prato, filtros, painel de acessibilidade, voz, diálogo da foto
├── translations/            # pt.json, en.json, es.json (inclui as frases dos comandos de voz)
└── static/
    ├── css/style.css        # tokens, foco, alto contraste, movimento reduzido, modo simplificado
    ├── js/                  # main, preferencias, foto, foco, anuncios
    │   └── voz/             # interpretador.js (puro, testável) + voz.js (Web Speech API)
    └── img/pratos/
migrations/                  # Alembic
tests/                       # pytest + tests/js (node --test)
docs/CONTRIBUTING.md
future/text_to_speech/
```

### Decisões de arquitetura

- **Alérgenos e dietas derivam dos ingredientes.** Cada ingrediente é cadastrado uma vez, com sua origem (vegetal, animal ou carne) e seus alérgenos. Um prato "vegano" ou "sem glúten" é calculado, nunca marcado à mão. Isso evita o erro mais perigoso num cardápio acessível: um prato marcado como seguro que não é.
- **Filtros rodam no banco.** As consultas continuam eficientes com cardápios grandes, e a URL filtrada pode ser salva ou compartilhada.
- **O servidor é a fonte da verdade das preferências.** Ele valida os valores e grava o cookie (`HttpOnly`). O JavaScript só pede a mudança e aplica o resultado, então não há regra duplicada entre Python e JS.
- **Tradução no servidor.** O HTML já chega no idioma certo, com `lang` correto, o que é importante para a pronúncia dos leitores de tela.

## Como contribuir

Veja [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md). Toda ajuda é bem-vinda, de correções de acessibilidade a novas features!

## Ideias para o futuro

- [ ] Painel admin para o restaurante editar pratos e ingredientes
- [ ] Tradução do conteúdo dos pratos (hoje só a interface é traduzida)
- [ ] Botão "Ouvir" em cada prato, sem depender de voz (ver `future/text_to_speech`)
- [ ] Fonte para dislexia (ex.: OpenDyslexic) como opção
- [ ] Mais idiomas
- [ ] Descrição em Libras (vídeo/avatar)
- [ ] API JSON pública do cardápio

## Licença

MIT
