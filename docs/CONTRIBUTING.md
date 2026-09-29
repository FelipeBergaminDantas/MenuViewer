# Como contribuir

Obrigado por querer ajudar a tornar cardápios digitais mais acessíveis! 🎉

## Antes de começar

1. Faça um fork do repositório
2. Crie uma branch: `git checkout -b feature/nome-da-sua-feature`
3. Instale as dependências: `pip install -r requirements-dev.txt`
4. Rode o projeto: `python run.py`

## Padrões do projeto

- **Acessibilidade em primeiro lugar**: toda nova UI precisa funcionar por teclado e ter foco visível. Use elementos HTML nativos (`button`, `a`, `details`, `dialog`, `label`) antes de recorrer a ARIA.
- **Sem texto fixo nos templates**: todo texto da interface vai em `app/translations/*.json` (nos três idiomas) e é usado com `t('chave')`.
- **Funcionar sem JavaScript sempre que possível**: formulários e links primeiro; o JS melhora a experiência.
- **Área de toque mínima**: 44×44px (`var(--alvo-min)`).
- **Contraste**: WCAG AA no tema padrão e no alto contraste. Use as variáveis de cor de `style.css`.
- **Alérgenos vêm dos ingredientes**: não crie campos como `sem_gluten` no prato; cadastre o ingrediente com seus alérgenos.
- **Mudou o modelo?** Gere uma migration: `flask --app run db migrate -m "descrição"`.
- **Sem frameworks JS pesados**: JS vanilla em módulos ES. Se isso precisar mudar, discuta antes numa issue.
- **Commits pequenos e descritivos**.

## Testes

Rode antes de abrir o Pull Request:

```bash
pytest
npm test
```

### Checklist manual de acessibilidade

Alguns pontos só dá para verificar no navegador:

- [ ] Navegar a página inteira só com `Tab` / `Shift+Tab`: a ordem segue a leitura e o foco é sempre visível
- [ ] Abrir e fechar a foto ampliada com `Enter` e `Esc`; o foco volta para o botão
- [ ] Testar com zoom do navegador em 200% e com a fonte em 200% no painel
- [ ] Testar com um leitor de tela (NVDA, VoiceOver ou TalkBack): cada prato é anunciado com nome, preço e descrição
- [ ] Testar no alto contraste e no modo simplificado

## Abrindo um PR

- Descreva o que mudou e por quê
- Se for uma feature de acessibilidade, explique qual necessidade ela atende
- Screenshots são bem-vindos, principalmente mostrando alto contraste / fontes maiores / modo simplificado

## Ideias em aberto

Veja a seção "Ideias para o futuro" no [README](../README.md) ou as [Issues](../../issues) abertas.
