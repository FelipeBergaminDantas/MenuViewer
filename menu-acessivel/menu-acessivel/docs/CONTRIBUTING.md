# Como contribuir

Obrigado por querer ajudar a tornar cardápios digitais mais acessíveis! 🎉

## Antes de começar

1. Dê um fork no repositório
2. Crie uma branch: `git checkout -b feature/nome-da-sua-feature`
3. Instale as dependências: `pip install -r requirements.txt`
4. Rode o projeto: `python run.py`

## Padrões do projeto

- **Acessibilidade em primeiro lugar**: toda nova UI precisa funcionar por teclado, ter `aria-label` quando necessário, e respeitar contraste mínimo (WCAG AA).
- **Área de toque mínima**: botões com no mínimo 44x44px.
- **Sem frameworks JS pesados**: mantemos JS vanilla no frontend por performance e simplicidade — se isso mudar, discuta antes numa issue.
- **Commits pequenos e descritivos**.

## Testes

Rode `pytest` antes de abrir o Pull Request.

## Abrindo um PR

- Descreva o que mudou e por quê
- Se for uma feature de acessibilidade, explique qual necessidade ela atende
- Screenshots são bem-vindos, principalmente mostrando o alto contraste / fontes maiores

## Ideias em aberto

Veja a seção "Ideias para o futuro" no [README](../README.md) ou as [Issues](../../issues) abertas. A pasta `future/text_to_speech` está reservada para quando começarmos essa feature — não implemente ainda, apenas documente ideias lá se quiser.
