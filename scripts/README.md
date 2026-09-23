# Manutenção dos ícones

Requer Python 3.10 ou superior. Usa somente a biblioteca padrão; não instala pacotes e não acessa a rede.

```sh
python scripts/generate_readme_icons.py
python scripts/validate_readme_assets.py
python -m unittest discover -s scripts -p 'test_*.py' -v
```

Os comandos localizam o repositório a partir do próprio script, independentemente do diretório de execução. O validador também aceita `--root CAMINHO` para testar outra cópia.

## Manifesto

`icon_manifest.json` registra nome, slug, cor, categoria e tipo de cada ícone:

- `kind: custom`: desenho local. Use `symbol` para uma geometria de `SYMBOLS` ou `label` para uma sigla curta. O gerador produz o cartão 64 × 64; o README exibe 48 × 48.
- `kind: brand`: logo de marca mantido manualmente. Inclui coleção, URL fixada em commit e licença da coleção. O gerador nunca grava esses arquivos.

Para adicionar um conceito, inclua uma entrada `custom`, execute o gerador e adicione a imagem individual com `alt`, `width="48"` e `height="48"` ao README. Para atualizar uma marca, revise a fonte e seus termos, atualize o SVG e a proveniência no manifesto. As licenças ficam em `.github/assets/licenses/`.

Use `python scripts/generate_readme_icons.py --check` para detectar alterações pendentes sem gravar arquivos. A integração contínua executa essa verificação, o validador e os testes em Linux, onde os caminhos também distinguem maiúsculas de minúsculas.

## Escopo da validação

O validador reconhece imagens HTML, Markdown inline e referências Markdown. Ignora URLs HTTP/HTTPS e exemplos em código; valida caminhos, capitalização, existência, alt e dimensões dos ícones HTML. Também confere as tags HTML usadas no README, todos os SVGs da pasta de ícones e a correspondência do manifesto.

SVGs precisam de XML válido e viewBox positivo. São rejeitados scripts, eventos, DTD, conteúdo ativo, CSS externo, URLs externas e referências internas inexistentes. Os cartões são autocontidos e não usam fontes externas.

A validação é voltada a este README: não substitui um parser completo de CommonMark nem um sanitizador genérico de conteúdo não confiável. Ela não faz requisições aos links externos nem testa entrega de e-mail. Verifique manualmente o conteúdo e a apresentação no GitHub antes de publicar.

## Origem e apresentação

Os 15 logos de marca são cópias de coleções comunitárias, não assets certificados como oficiais: 12 do Devicon e 3 do Simple Icons. As formas foram preservadas e inseridas em cartões locais. Nomes e marcas pertencem aos respectivos titulares; sua presença identifica as ferramentas e não indica endosso.

Power BI, Excel, ChatGPT e Microsoft Copilot usam símbolos próprios de gráfico, planilha, conversa e assistente, respectivamente. Esses produtos não tinham um asset adequado disponível nas versões consultadas das duas coleções. Codex e os conceitos técnicos também usam desenhos próprios. Nenhum desses desenhos é apresentado como logo oficial.

O fundo suave `#F1F5F9`, a borda `#94A3B8`, os desenhos escuros e o espaçamento comum mantêm o contraste em páginas claras e escuras. Todos os arquivos têm título SVG; o README também fornece alt e os nomes em texto.

## Contatos

Os dois botões em `.github/assets/buttons/` são SVGs locais mantidos manualmente, com degradê, brilho e relevo estáticos, reutilizados no cabeçalho e no rodapé. O validador também verifica esses assets por estarem referenciados no README. O gerador de ícones de tecnologias não altera os botões.
