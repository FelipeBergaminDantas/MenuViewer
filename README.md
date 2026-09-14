<img width="2752" height="1536" alt="Gemini_Generated_Image_jt1scljt1scljt1s" src="https://github.com/user-attachments/assets/d35ca042-1c81-4b05-9664-2618044e5cf5" />


# 🍽️ Cardápio Acessível

Um sistema de cardápio digital para restaurantes com foco em **acessibilidade**, feito para ser simples, leve e fácil de estender via colaborações no GitHub.

## Objetivo

Tornar a visualização de um menu digital acessível para o maior número possível de pessoas, através de:

- **Acessibilidade visual**: aumento/diminuição de fonte, alto contraste, zoom em imagens dos pratos
- **Acessibilidade motora/cognitiva**: botões grandes (área mínima de toque 44x44px), linguagem simples, opção de reduzir animações
- **Inclusão de idioma**: seletor de idioma via bandeiras (PT / EN / ES)
- *(planejado)* **Text-to-speech**: leitura em voz alta do cardápio — ver pasta `future/text_to_speech`

## Stack

- **Backend**: Flask + Flask-SQLAlchemy
- **Banco**: SQLite (arquivo local, zero configuração)
- **Frontend**: Jinja2 + HTML semântico + CSS + JS vanilla (sem frameworks pesados, por performance e acessibilidade)

## Como rodar

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Acesse `http://127.0.0.1:5000`.

## Estrutura do projeto

```
app/
├── models.py           # Categoria, Prato
├── database.py         # config SQLAlchemy
├── seed.py             # dados de exemplo
├── routes/menu.py       # rotas do cardápio
├── templates/          # HTML (Jinja2)
└── static/
    ├── css/             # estilos + alto contraste
    ├── js/              # fonte, contraste, zoom, idioma, reduzir movimento
    ├── locales/         # traduções (pt/en/es)
    └── img/             # imagens de pratos e bandeiras

future/text_to_speech/  # reservado para funcionalidade futura de leitura em voz alta
```

## Como contribuir

Veja [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md). Toda ajuda é bem-vinda — de correções de acessibilidade a novas features!

## Ideias para o futuro

- [ ] Text-to-speech (leitura do cardápio)
- [ ] Painel admin para o restaurante editar pratos
- [ ] Modo de navegação simplificada (menos elementos por tela)
- [ ] Fonte para dislexia (ex: OpenDyslexic) como opção
- [ ] Mais idiomas
- [ ] Descrição de Libras (vídeo/avatar)

## Licença

MIT
