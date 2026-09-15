# Marca

Arte da identidade visual da Hinove usada pela janela do Apurabot.

| arquivo | para que serve |
|---|---|
| `hinove.png` | logo da Hinove, no canto superior direito da janela |

## Como o arquivo chega na tela

A janela é **um arquivo só** — `src/apurabot/web/pagina.html`. Ela abre com a
máquina desconectada da internet e o servidor local só entrega essa página,
então nenhuma imagem é buscada por URL.

O PNG daqui é convertido para `data:` URI e embutido dentro do HTML por:

```
python3 marca/embutir_logo.py
```

Rode o script sempre que trocar o `hinove.png`. Enquanto ele não existir, a
janela desenha o logo em SVG — as três bolas e o wordmark — que é o
suficiente, mas não é a arte oficial.

## O que o arquivo precisa ter

- **PNG** com fundo transparente
- **pelo menos 1200 px de largura** — a janela mostra em 280 px, mas em tela
  HiDPI ele é renderizado no dobro
- **até uns 300 KB** — vira base64 dentro do HTML, o que engorda uns 33%
