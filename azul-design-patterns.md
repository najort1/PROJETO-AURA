# Inventário de Design Patterns — Azul Viagens e Azul Fidelidade

> **Fonte da análise:** duas capturas de página inteira fornecidas pelo usuário. A primeira representa uma página de **Azul Fidelidade**; a segunda, a página inicial de **Azul Viagens**. O documento descreve padrões visíveis nas imagens, não o código-fonte original.
>
> **Nota sobre precisão:** cores, espaçamentos e proporções abaixo são aproximações visuais para recriação. Não é possível confirmar apenas pelas capturas a fonte exata, os breakpoints, os estados reais de interação ou os valores de CSS.

## Sumário

1. [Leitura geral do sistema](#1-leitura-geral-do-sistema)
2. [Tokens visuais aproximados](#2-tokens-visuais-aproximados)
3. [Tipografia e hierarquia](#3-tipografia-e-hierarquia)
4. [Layout, containers e espaçamento](#4-layout-containers-e-espaçamento)
5. [Cabeçalho e navegação](#5-cabeçalho-e-navegação)
6. [Padrões da página Azul Viagens](#6-padrões-da-página-azul-viagens)
7. [Padrões da página Azul Fidelidade](#7-padrões-da-página-azul-fidelidade)
8. [Componentes transversais](#8-componentes-transversais)
9. [Iconografia, imagens e tratamento visual](#9-iconografia-imagens-e-tratamento-visual)
10. [Interações e estados a reproduzir](#10-interações-e-estados-a-reproduzir)
11. [Acessibilidade e comportamento responsivo](#11-acessibilidade-e-comportamento-responsivo)
12. [Checklist de implementação](#12-checklist-de-implementação)
13. [Observações e limitações](#13-observações-e-limitações)

---

## 1. Leitura geral do sistema

As capturas pertencem ao ecossistema da Azul, mas representam **duas experiências com objetivos diferentes** e pequenas diferenças de linguagem visual.

### Padrões compartilhados

- Predominância de azul como cor de marca e de navegação.
- Superfícies brancas, fundos claros e conteúdo centralizado.
- Uso de imagens grandes para vender uma experiência: destinos, hotéis, pessoas e viagens.
- Hierarquia organizada em seções verticais com títulos curtos.
- CTAs de alto contraste; o azul aparece com frequência em ações institucionais e a página de viagens usa rosa/magenta para a ação principal de busca.
- Cards, carrosséis, faixas promocionais, grupos de logotipos e chamadas para outras áreas do site.
- Cabeçalho e rodapé extensos, voltados à navegação institucional, atendimento e confiança.

### Diferença de personalidade por produto

| Área | Azul Viagens | Azul Fidelidade |
|---|---|---|
| Objetivo principal | Pesquisar e comprar viagens | Entender pontos, categorias e benefícios |
| Linguagem visual | Editorial, aspiracional, comercial | Informativa, explicativa e orientada a programa |
| Cor de destaque | Azul + rosa/magenta; amarelo-lima em uma campanha | Azul em diferentes intensidades |
| Elemento dominante | Banner de destino e formulário de busca | Hero com pessoa, módulos informativos e tabela de categorias |
| Padrões recorrentes | Pesquisa, cards com preço, mosaico de experiências, carrossel de ofertas | Cards de explicação, degraus/tier cards, ícones de benefício, banners educativos e parceiros |

**Princípio central:** o sistema combina uma base institucional sóbria com áreas promocionais visualmente fortes. As imagens e os blocos coloridos atraem a atenção; superfícies brancas e textos menores sustentam a navegação e a informação.

---

## 2. Tokens visuais aproximados

Os valores são uma **paleta de referência estimada visualmente**, não tokens extraídos do CSS real. Recomenda-se validar os tons com amostragem de pixels ou com os arquivos oficiais da marca antes de usar em produção.

### 2.1 Cores

| Token sugerido | Valor aproximado | Uso observado |
|---|---|---|
| `azul-primary` | `#008BC4` | Azul de destaque em módulos da página de fidelidade |
| `azul-action` | `#0874B5` | Botões azuis e links de ação |
| `azul-sky` | `#2DA6D4` | Áreas claras/iluminadas em composições azuis e banners |
| `azul-deep` | `#033774` | Fundos e elementos institucionais escuros |
| `azul-navy` | `#00345F` a `#0B3558` | Cabeçalhos, texto institucional e faixas escuras |
| `magenta-cta` | Aproximadamente `#E832A5` | Botão de busca da Azul Viagens e preços em destaque |
| `lime-campaign` | Amarelo-lima vivo, aproximadamente `#D8ED00` | CTA promocional sobre o hero de resorts |
| `text-primary` | `#1E2A30` | Títulos e texto principal na área de viagens |
| `text-secondary` | Cinza médio | Metadados, subtítulos, informações auxiliares |
| `surface` | `#FFFFFF` | Cards, formulário, cabeçalho e blocos de conteúdo |
| `canvas` | `#F8F9FA` | Fundo geral cinza muito claro na página de viagens |
| `border-subtle` | Cinza claro, aproximadamente `#E2E6E9` | Bordas de campos, cards e divisórias |

### 2.2 Regras de uso da cor

- **Azul escuro:** navegação, identidade, títulos de maior peso e faixas de suporte.
- **Azul médio/claro:** ações secundárias, ícones, links e conteúdo informativo.
- **Rosa/magenta:** ação comercial principal na busca e números que precisam chamar a atenção, como preços.
- **Amarelo-lima:** usado pontualmente para campanha; não deve competir com todos os outros CTAs.
- **Branco:** separa visualmente os componentes e mantém o conteúdo de formulário legível.
- **Cinza muito claro:** dá contraste suave entre o canvas e os componentes brancos sem criar uma interface escura.

A captura da Azul Fidelidade usa uma escala maior de azuis, de ciano a azul-marinho, para diferenciar seções e níveis. A página de viagens é predominantemente clara, deixando a fotografia e o magenta criar os pontos de atenção.

### 2.3 Forma, borda e profundidade

- Cards majoritariamente retangulares, com cantos retos ou levemente arredondados.
- Campos de formulário com borda cinza clara e arredondamento discreto.
- Botões com cantos suavemente arredondados; o CTA de campanha sobre o hero usa formato de pílula.
- Sombras discretas ou quase ausentes; a sobreposição do formulário ao banner cria profundidade principalmente pelo contraste branco sobre a fotografia.
- Separadores horizontais finos para dividir áreas do rodapé e blocos informativos.
- Nas duas imagens, não se observa um sistema de cartões fortemente elevado: a organização depende mais de alinhamento, espaço e contraste do que de sombras.

**Tokens de forma recomendados para uma recriação fiel:** `radius-sm` de 3–5 px para inputs/cards, `radius-md` de 6–10 px para painéis e botões, `radius-pill` de 999 px para badges e CTA de campanha. São sugestões práticas, não medidas verificadas.

---

## 3. Tipografia e hierarquia

A fonte exata não pode ser determinada com segurança pela resolução das capturas. A aparência é de uma família **sans-serif**, semelhante a Arial/Roboto ou outra sans corporativa.

### Hierarquia observada

1. **Headline do hero:** grande, branca, em negrito e com quebra em poucas linhas.
2. **Títulos de seção:** tamanho intermediário, escuros, alinhados à esquerda e com peso normal a seminegrito.
3. **Título de card:** pequeno, com contraste suficiente para identificação rápida.
4. **Metadados e apoio:** texto pequeno para duração, destino, preço-base, classe, detalhes e links auxiliares.
5. **Navegação:** pequena e compacta para acomodar muitos destinos e categorias.
6. **CTA:** texto curto, com peso forte e contraste alto.

### Convenções

- Títulos costumam usar capitalização de frase, em vez de blocos inteiros em caixa alta.
- Rótulos do formulário aparecem em caixa alta e em tamanho menor que o conteúdo do campo.
- Preços e percentuais promocionais são visualmente destacados pelo uso de magenta ou de fonte maior.
- Textos sobre fotografia recebem contraste adicional por sombra/escurecimento da imagem ou por uma área de fundo mais escura.
- Algumas áreas informativas da fidelidade parecem utilizar textos muito pequenos. Para uma implementação atual, convém manter a linguagem visual sem repetir tamanhos que prejudiquem a legibilidade.

### Escala sugerida para reconstrução

| Uso | Escala inicial sugerida |
|---|---:|
| Headline do hero | 28–40 px desktop |
| Título de seção | 18–24 px |
| Título de card | 14–16 px |
| Texto de corpo | 14–16 px |
| Metadados | 11–13 px, evitando ficar abaixo de 12 px quando possível |
| Rótulo de formulário | 10–12 px, preferencialmente 12 px ou mais |
| Texto de botão | 13–16 px, semibold/bold |

Essa escala é uma base para implementação, não uma medição exata das imagens.

---

## 4. Layout, containers e espaçamento

### 4.1 Estrutura geral

- Cabeçalho branco ocupando toda a largura.
- Conteúdo principal centralizado e mais estreito que a viewport.
- Hero largo, com imagem de borda a borda dentro do container principal, não necessariamente até as extremidades da tela.
- Seções em pilha vertical, alternando fundo claro, branco e blocos de cor.
- Rodapé mais denso, composto por muitas colunas de links, informações e selos.

### 4.2 Grid

**Azul Viagens**

- Busca de viagem organizada em várias colunas de formulário.
- Linha de quatro cards de destino/oferta.
- Grade editorial de duas colunas com imagens de proporção larga.
- Carrossel final de quatro cards de ofertas.
- Rodapé em colunas distintas, com links, parceiros, moedas/cotações e selo de reputação.

**Azul Fidelidade**

- Área principal de conteúdo visualmente estreita e centralizada.
- Seções com três cards explicativos.
- Grade de cinco cartões de categorias/níveis em sequência cromática.
- Fileiras de benefícios com quatro itens e ícones.
- Blocos promocionais lado a lado, listas de parceiros/logotipos e banners horizontais.

### 4.3 Espaçamento

O ritmo visual é baseado em separação clara entre seções e espaçamentos internos relativamente compactos nos módulos densos.

Tokens recomendados para aproximação:

- `space-1`: 4 px
- `space-2`: 8 px
- `space-3`: 12 px
- `space-4`: 16 px
- `space-5`: 24 px
- `space-6`: 32 px
- `space-7`: 48 px
- `space-8`: 64 px

Aplicação sugerida:

- 8–16 px entre rótulo e campo.
- 12–20 px entre elementos dentro de cards.
- 24–40 px entre título de seção e o conteúdo.
- 48–72 px entre seções em desktop.
- Container central com largura máxima configurável e padding lateral fluido.

A captura da Azul Viagens apresenta um grande intervalo vertical entre os cards iniciais e a seção editorial. Como isso pode ser efeito de carregamento, publicidade ou composição original, **não trate esse vazio como regra obrigatória** sem observar o site em funcionamento.

---

## 5. Cabeçalho e navegação

### 5.1 Azul Viagens

O cabeçalho possui duas camadas visuais:

**Linha superior de utilidades**

- Logo Azul Viagens à esquerda.
- Telefone de atendimento em rosa/magenta.
- Ícones de canais/redes sociais.
- Link para consultar reserva.
- Botão de acesso/login em magenta.
- Seletores compactos de moeda e idioma.

**Navegação principal**

- Links horizontais com categorias de viagem.
- Item atual destacado por cor/peso tipográfico mais escuro.
- Alguns itens possuem chevron para indicar menu suspenso.
- Navegação com tipografia pequena e espaçamento horizontal compacto.

**Padrão:** separar as utilidades de conta/atendimento da navegação por conteúdo, mantendo ambas no mesmo cabeçalho branco.

### 5.2 Azul Fidelidade

- Barra superior mais densa, com identidade Azul, links de áreas do programa e pequenas ações utilitárias.
- Abaixo, faixa branca de atalhos que agrupa ícones com rótulos.
- O menu de atalhos cria uma segunda camada de navegação, distinta do menu principal.

### 5.3 Regras de implementação

- Manter a marca sempre alinhada ao início do container, sem centralizar o logo isoladamente.
- Agrupar telefone, conta, moeda e idioma como utilidades, não como categorias primárias.
- Representar menus expansíveis com chevrons e estados de foco/abertura.
- Garantir que o item ativo tenha uma indicação além de cor, por exemplo peso da fonte ou sublinhado.
- Em telas estreitas, converter as linhas horizontais em navegação recolhida e manter acesso às tarefas mais importantes. Esse comportamento é uma recomendação; a captura não permite confirmar o breakpoint original.

---

## 6. Padrões da página Azul Viagens

### 6.1 Hero/banner de campanha

**Estrutura:** imagem panorâmica de resort, headline branca, etiqueta de campanha, CTA sobreposto, controles de navegação lateral e indicadores de slide.

**Características visuais:**

- Fotografia é o elemento dominante.
- Texto de destaque posicionado dentro do banner, não numa coluna separada.
- Uma etiqueta azul-escura com título da campanha e subtítulo amarelo.
- CTA em formato de pílula amarelo-lima com texto azul.
- Setas de navegação rosas nas margens externas ao banner.
- Indicadores circulares próximos à parte inferior central.

**Comportamento de componente esperado:**

- Carrossel com estados de slide ativo/inativo.
- CTA navegável para a campanha.
- Controles acessíveis por teclado e com nomes compreensíveis por leitor de tela.
- Imagens com foco/corte controlado para preservar o assunto principal.

### 6.2 Painel de busca sobreposto ao hero

É o componente funcional mais importante da página.

**Composição:**

1. Caixa branca larga que sobrepõe a parte inferior do hero.
2. Abas por tipo de produto: pacotes, hospedagens, ingressos/passeios, carros, traslados e seguros.
3. Subopções dentro da categoria selecionada, como combinação de voo + hotel.
4. Formulário de busca em grid.
5. Opções auxiliares e expansão de “mais opções”.

**Campos visíveis na captura:**

- Cidade de origem.
- Cidade de destino.
- Aeroporto de destino.
- Data de saída e volta.
- Apartamento/passageiros.
- Classe.
- Franquia de bagagem.
- Opções complementares, incluindo casa de temporada e escolha de exibição de valores.

**Estilo dos campos:**

- Fundo branco, borda cinza clara e cantos suavemente arredondados.
- Label pequeno em caixa alta acima do campo.
- Placeholder em cinza.
- Ícone contextual dentro do campo, como localização, calendário ou seta de dropdown.
- O magenta destaca ícones selecionados e o botão primário.
- Botão “Buscar” visualmente forte, separado dos inputs e alinhado à direita na linha principal.

**Padrões de interação a preservar:**

- Abas com estado ativo e inativo claro.
- Campos de data com seletor de calendário.
- Dropdowns com indicador de expansão.
- Contador/seleção de passageiros de uso direto.
- “Mais opções” expansível.
- Validação e mensagens de erro alinhadas ao campo, sem depender só da cor.

### 6.3 Cards compactos de destinos e ofertas

**Layout:** faixa horizontal com quatro cards na captura.

**Anatomia do card:**

- Imagem de destino na parte superior.
- Badge branco em formato de pílula com duração (dias/noites) no canto superior esquerdo.
- Ícones brancos no canto superior direito, representando componentes/inclusões do pacote.
- Área inferior branca com nome do destino e dados de preço.
- Preço destacado em magenta, com a expressão de preço-base em texto menor.
- Borda fina clara separando o card do canvas.

**Padrões:**

- Imagens com a mesma altura dentro da fileira.
- Informação essencial visível sem abrir o card: duração, destino e preço.
- Metadados compactos, sem dominar a imagem.
- Card inteiro deve funcionar como alvo clicável, caso navegue para oferta.

### 6.4 Seções com título e sublinhado magenta

Títulos como “Ofertas para conhecer novos lugares” e “Muito mais que aéreo + hotel” usam:

- Alinhamento à esquerda.
- Texto escuro em tamanho intermediário.
- Pequeno traço rosa/magenta logo abaixo do título.
- Espaço visível antes do conteúdo subsequente.

Esse traço funciona como assinatura visual da seção e deve ter comprimento curto, sem se estender por toda a largura.

### 6.5 Mosaico editorial de experiências

**Estrutura:** grade de duas colunas e várias linhas de tiles panorâmicos.

**Anatomia:**

- Fotografia ocupa todo o tile.
- Texto branco sobreposto, normalmente próximo à parte inferior esquerda.
- Título curto do tema/destino.
- Subtítulo menor em alguns tiles.
- Escurecimento local/overlay sobre a imagem para melhorar a leitura.
- Pequeno gutter branco entre tiles.

**Temas representados:** campanhas, ecoturismo, corridas, resorts, cruzeiros e parques. A regra relevante é o padrão do mosaico, e não as categorias específicas.

**Uso:** navegação exploratória quando o usuário ainda não decidiu uma oferta exata.

**Regras:** manter proporções consistentes, aplicar overlay suficientemente escuro e preservar o texto numa área previsível do card.

### 6.6 Carrossel “Ofertas Azul”

- Título da seção com o mesmo sublinhado magenta.
- Setas de avançar/voltar posicionadas no lado direito do título/da seção.
- Cards em linha horizontal.
- Cada card combina banner fotográfico azul, badges de duração, ícones de inclusões, nome do hotel/destino e preço-base.
- Preço grande em magenta; localidade e tipo de pacote em texto escuro menor.
- Alguns cards aparentam apresentar uma camada de escurecimento/estado de hover, mas a captura estática não comprova o comportamento.

**Design pattern:** `horizontal offer carousel` com hierarquia de preço bastante evidente.

### 6.7 Rodapé da Azul Viagens

Rodapé extenso, dividido em regiões:

1. Lista de links institucionais e de suporte.
2. Bloco de parceiros.
3. Indicadores de moedas/cotações.
4. Selo de reputação/avaliações.
5. Linha final com marca, informações legais e créditos da plataforma.

**Estilo:** fundo branco, separação por espaço e linha horizontal, texto pequeno e pouco destaque cromático. O rodapé prioriza densidade e cobertura de conteúdo em vez de impacto visual.

---

## 7. Padrões da página Azul Fidelidade

### 7.1 Hero com fundo azul e pessoa em destaque

- Fundo panorâmico em gradiente/textura azul.
- Pessoa posicionada no lado direito, com grande recorte circular azul atrás da cabeça.
- Elementos de viagem pequenos ao fundo, reforçando o contexto da marca.
- Caixa de texto promocional no lado esquerdo, usando azul mais escuro e texto branco.
- Pequenos controles/indicadores de carrossel dentro do bloco inferior.

**Padrão:** hero humano/emocional combinado com uma mensagem curta sobre o programa. Diferentemente do banner de resorts, a cena prioriza uma pessoa e um contexto aspiracional, não um produto específico.

### 7.2 Barra de atalhos com ícones

Logo abaixo do hero há uma seção branca com título centralizado e uma fileira de atalhos:

- Ícone azul.
- Rótulo curto.
- Separadores verticais finos entre grupos.
- Indício de navegação adicional por seta/círculo no lado direito.

**Uso:** dar acesso rápido às ações e áreas importantes sem misturar esses atalhos com o conteúdo editorial abaixo.

### 7.3 Seção azul de descoberta/consulta de pontos

- Faixa horizontal com fundo azul saturado.
- Título central branco.
- Módulo branco de abas e cards destacado contra o fundo azul.
- Duas abas na parte superior do painel; a ativa recebe fundo claro/branco e a inativa aparência cinza.
- Cards de pessoas/benefícios em linha, com imagem, título, breve explicação e link de ação.
- Controles discretos de navegação no topo/lateral do painel.
- CTA secundário em uma faixa branca separada logo abaixo.

**Padrão:** agrupar uma tarefa de consulta e conteúdo educativo num módulo de alto contraste, sem que o fundo colorido se estenda para cada card interno.

### 7.4 Grupos de cards explicativos

A página intercala seções brancas com cards dispostos em três colunas.

**Estrutura típica:**

- Título de seção centralizado.
- Texto introdutório curto.
- Cards com ícone ou pequeno símbolo azul, título e descrição compacta.
- Link de ação em azul.
- Em alguns grupos, indicadores/setas de carrossel abaixo.

**Função:** explicar como funciona o programa, como começar e quais ações geram valor. Os cards são informativos, visualmente leves e com pouco contraste de fundo.

### 7.5 Sequência de passos

Há uma área com três etapas horizontais para orientar o usuário.

- Cada etapa tem um marcador numerado dentro de uma forma contornada/ovalada.
- Texto descritivo compacto.
- Botão azul embaixo.
- Colunas separadas por espaço, com uma linha de leitura horizontal.

**Padrão:** `three-step explainer`. O número estabelece ordem; texto e botão oferecem contexto e ação para cada etapa.

### 7.6 Cartões de categorias/níveis de fidelidade

Uma fileira de cinco cartões verticais é um dos componentes mais distintivos da página.

**Anatomia:**

- Cartões da mesma altura, alinhados lado a lado.
- Escala de cores que começa em ciano claro e progride por azuis até marinho.
- Ícone e identificação da categoria no topo.
- Conteúdo sobre metas, pontuação, milhas/pontos ou vantagens no corpo.
- Separadores horizontais internos.
- Números de maior valor visual destacados com tamanho maior.
- O último cartão tem um selo rosa “Novo”, indicando novidade.

**Design pattern:** `tier comparison cards` / comparação de níveis. A cor cria uma progressão visual e ajuda a diferenciar as categorias.

**Regras de reconstrução:**

- Repetir a mesma estrutura para todos os níveis.
- Usar cor e texto para comunicar o nível, sem depender apenas de cor.
- Preservar alinhamento de títulos, metas e valores entre os cartões.
- Em mobile, evitar comprimir cinco colunas com texto minúsculo; transformar em carrossel ou lista expansível.

### 7.7 Bloco editorial explicativo com chamada de ajuda

Depois da comparação de níveis, aparece uma área de texto introdutório/explicativo e, em seguida, uma faixa de apoio:

- Ícone informativo à esquerda.
- Pergunta ou chamada em negrito.
- Descrição curta.
- Botão azul à direita.
- Borda ou divisor fino na parte superior/inferior.

**Padrão:** barra de ajuda contextual que permite esclarecer uma questão sem interromper a sequência de conteúdo.

### 7.8 Fileira de benefícios com ícones

- Título centralizado.
- Quatro colunas de benefício.
- Ícones azuis acima dos rótulos.
- Rótulos curtos com centralização.
- Uma CTA azul abaixo da fileira.

**Função:** apresentar benefícios de forma escaneável. O ícone ajuda a separar conceitos e reduz a dependência de parágrafos longos.

### 7.9 Banners promocionais lado a lado

- Dois retângulos horizontais de dimensões semelhantes.
- Fotografia/arte promocional dentro do banner.
- Azul como fundo ou tom dominante.
- Conteúdo textual integrado à imagem, com marca, chamada ou benefício.
- Pequenas legendas/links logo abaixo em alguns casos.

Esse padrão funciona como uma vitrine para campanhas ou produtos relacionados ao programa.

### 7.10 Faixas de parceiros e marcas

A página apresenta mais de uma região de parceiros, agrupados por categoria.

- Título centralizado indicando a relação entre marcas e o programa.
- Fileiras de logotipos em suas cores originais.
- Espaçamento horizontal regular entre marcas.
- CTA azul centralizado abaixo de determinados grupos.
- Divisão por assunto: parceiros de acúmulo/compra e parceiros relacionados a viagens, conforme sugerido pelos títulos visíveis.

**Padrão:** `logo cloud` segmentado por categoria. A cor original dos parceiros é preservada, enquanto o CTA e os títulos seguem o azul institucional.

### 7.11 Banner de campanha com divisão texto/imagem

- Banner horizontal com lado textual em azul escuro.
- Fotografia no lado direito.
- Título e texto brancos no painel esquerdo.
- Botão claro ou de alto contraste.
- Cantos discretamente arredondados.

**Padrão:** `split promotional banner`. A divisão retangular ajuda a equilibrar mensagem e fotografia.

### 7.12 Suporte, FAQ e chamadas finais

- Faixa branca com ícone, pergunta e botão azul.
- Faixa de suporte com fundo azul-marinho, ícone de conversa/documento, frase curta e botão branco/claro.
- Links relacionados agrupados antes do rodapé.
- Elementos de navegação/rodapé densos e divididos por linhas horizontais.

**Padrão:** finalizar a página com ações de suporte, links relacionados e só depois as informações institucionais completas.

### 7.13 Rodapé da Azul Fidelidade

Comparado ao da Azul Viagens, é mais denso e institucional:

- Grupos de navegação em várias colunas.
- Listas de links pequenos.
- Blocos de informação institucional/legal.
- Redes sociais e ícones.
- Sinais de pagamento/selos ou materiais de marca.
- Barra final com identidade Azul e elementos de confiança/download.

A densidade visual do rodapé é significativamente maior que a do conteúdo principal. Deve haver hierarquia por colunas e títulos para impedir que vire uma lista única sem estrutura.

---

## 8. Componentes transversais

### 8.1 Botões

Tipos visíveis ou sugeridos pelas capturas:

- **Primário azul:** ação institucional ou de continuidade.
- **Primário magenta:** pesquisa/compra na Azul Viagens.
- **CTA de campanha lima:** botão sobre o hero.
- **Secundário claro:** botão branco ou com borda, especialmente em banners escuros.
- **Links textuais:** ações de menor prioridade, geralmente azuis.

Regras:

- Texto curto e orientado à ação.
- Contraste alto entre texto e fundo.
- Altura consistente dentro da mesma família de componentes.
- Estados hover, focus, active e disabled definidos explicitamente.
- Não usar magenta, azul e lima ao mesmo tempo para várias ações com a mesma importância.

### 8.2 Cards

Famílias encontradas:

1. Card de destino com preço.
2. Card promocional com foto e texto sobreposto.
3. Card informativo com ícone e texto.
4. Card de nível/tier.
5. Card em carrossel de oferta.

Cada família deve ter uma anatomia própria e consistente. Evitar transformar todos em um card genérico com imagem em cima, pois as capturas usam composição diferente para propósitos diferentes.

### 8.3 Badges e etiquetas

- Pílula branca com duração de viagem sobre imagem.
- Etiqueta de campanha azul sobre o hero.
- Selo de novidade em rosa.
- Pequenas etiquetas de preço/condição em cards.

Badges carregam informação curta. Não devem conter texto descritivo extenso nem competir com a headline.

### 8.4 Carrosséis

Padrões recorrentes:

- Setas laterais ou agrupadas à direita da seção.
- Indicadores de slide no hero.
- Fileiras horizontais de cards.
- Navegação discreta, com o conteúdo visual permanecendo como foco.

Comportamentos recomendados:

- Explicar a ação dos controles por `aria-label`.
- Manter o item ativo e a posição navegável por teclado.
- Evitar autoplay rápido; permitir pausar caso haja movimento automático.
- Em dispositivos touch, oferecer swipe sem eliminar controles visíveis.

### 8.5 Faixas de CTA e alertas informativos

- Ícone ou pequeno símbolo à esquerda.
- Texto principal e descrição no centro.
- Botão à direita.
- Fundo branco, bordas/divisórias discretas ou fundo azul-escuro em faixas de suporte.

Esse padrão pode ser usado para tirar dúvidas, explicar benefícios ou conduzir o usuário para uma ação seguinte.

### 8.6 Grupos de logos

- Logos preservam suas cores originais.
- São organizados em linhas com espaçamento constante.
- Título centralizado acima.
- CTA abaixo quando existe navegação para a lista completa.

O sistema deve tratar logos como imagens com altura visual normalizada; logos com proporções diferentes precisam de `object-fit: contain` e limites de largura/altura.

---

## 9. Iconografia, imagens e tratamento visual

### Iconografia

- Ícones simples de traço, geralmente em azul nas áreas informativas.
- Ícones no cabeçalho pequenos e compactos.
- Ícones de avião, hotel, calendário, localização, atendimento e benefícios aparecem associados a rótulos ou metadados.
- Em cards promocionais, ícones brancos são sobrepostos à fotografia.
- A imagem de fidelidade utiliza ícones lineares em atalhos e cards explicativos.

**Regra:** ícones precisam compartilhar espessura de linha e estilo; misturar ícones preenchidos com lineares sem regra clara quebraria a consistência.

### Fotografia e imagens

- Fotografia ampla e aspiracional no hero.
- Destinos e hotéis em cards com proporções consistentes.
- Tiles editoriais com overlay escuro para acomodar títulos brancos.
- Banners de campanhas podem incluir arte publicitária já composta, diferente das imagens editoriais simples.
- Na página de fidelidade, pessoas e elementos de viagem são usados para dar dimensão emocional à proposta.

### Tratamento recomendado

- `object-fit: cover` em banners e cards fotográficos.
- Ponto focal definido por imagem, usando posicionamento específico quando o sujeito não puder ser cortado.
- Gradiente/overlay escuro na área de texto de tiles.
- Não aplicar o mesmo overlay uniformemente quando o conteúdo da imagem já possui contraste suficiente.
- Não usar imagem meramente decorativa no lugar de texto que precisa ser selecionável, pesquisável ou acessível.

---

## 10. Interações e estados a reproduzir

As imagens são estáticas; esta seção lista estados que o design sugere ou que são necessários para implementar os padrões de forma funcional, **não interações confirmadas por teste do site**.

| Componente | Estados/ações a prever |
|---|---|
| Menu com chevron | Fechado, aberto, foco por teclado, item selecionado |
| Abas de produto | Ativa, inativa, foco; conteúdo correspondente a cada aba |
| Input de texto | Vazio, preenchido, foco, erro, desabilitado |
| Campo de data | Data escolhida, calendário aberto, faixa inválida |
| Passageiros/apartamentos | Contador, mínimo/máximo, confirmação |
| Dropdown | Fechado, aberto, opção selecionada |
| Botão principal | Normal, hover, focus, pressed, loading, disabled |
| Hero/carrossel | Slide ativo, anterior/próximo, indicadores ativos |
| Carrossel de ofertas | Primeiro/último item, navegação, swipe/touch |
| Card clicável | Hover/focus visível e destino de navegação claro |
| Mais opções | Recolhido, expandido, campos extras visíveis |
| Banner/CTA | Área clicável definida, sem capturar cliques de controles internos indevidamente |

### Feedback funcional recomendado para a busca

- Validar campos obrigatórios com mensagens explícitas.
- Exibir erros junto ao campo e preservar os valores digitados.
- Mostrar estado de carregamento após a ação de busca.
- Evitar que o botão pareça desabilitado quando o usuário pode preencher o formulário.
- Fornecer uma confirmação compreensível ao alterar abas se os campos disponíveis mudarem.

---

## 11. Acessibilidade e comportamento responsivo

O desktop é a única apresentação que pode ser analisada diretamente. Os pontos abaixo são recomendações de implementação, não descrição de um comportamento mobile confirmado.

### Acessibilidade

- Contraste AA para texto normal e controles.
- Não depender exclusivamente de cores para indicar seleção, nível, erro ou estado.
- Alvo de toque ideal de pelo menos 44 × 44 px, especialmente para setas, ícones de cabeçalho e controles de data.
- Labels persistentes nos inputs; não depender apenas de placeholder.
- Alt text útil para fotografias informativas; `alt=""` para imagens decorativas.
- Foco de teclado visível em links, tabs, botões e menus.
- Carrosséis controláveis por teclado e com nomes acessíveis.
- Headings em ordem lógica, evitando usar apenas tamanho de fonte para simular hierarquia.
- Texto integrado a banners precisa ter alternativa acessível, se estiver incorporado na imagem.
- Cards clicáveis devem ter comportamento previsível e não conter links/botões aninhados de forma inválida.

### Regras responsivas recomendadas

**Cabeçalho**

- Desktop: duas camadas horizontais como nas capturas.
- Tablet/mobile: reduzir utilidades e agrupar navegação num menu; manter telefone/acesso ou a ação de maior valor de negócio.

**Hero**

- Preservar a headline e o CTA mesmo se a imagem tiver de trocar de enquadramento.
- Ajustar `object-position` por breakpoint.
- Em telas estreitas, não deixar texto e CTA sobrepostos a áreas visualmente complexas da fotografia.

**Formulário de busca**

- Desktop: grid de várias colunas.
- Tablet: duas colunas com CTA facilmente encontrado.
- Mobile: campos empilhados, grupos de data lado a lado apenas quando houver espaço, CTA em largura integral.
- Abas horizontais podem rolar, mas o estado ativo deve continuar claramente visível.

**Cards de viagem**

- Desktop: quatro cards em linha.
- Tablet: dois cards por linha.
- Mobile: carrossel horizontal ou lista vertical; não reduzir os cards até que os preços se tornem ilegíveis.

**Mosaico editorial**

- Desktop: duas colunas.
- Mobile: uma coluna ou tiles com proporção menor, mantendo títulos e overlays legíveis.

**Categorias da fidelidade**

- Cinco tiers não devem ser comprimidos numa linha estreita. Usar carrossel com snap, navegação acessível ou cartões empilhados.

**Rodapé**

- Desktop: várias colunas.
- Mobile: grupos recolhíveis com cabeçalhos claros e áreas de toque confortáveis.

---

## 12. Checklist de implementação

### Fundação visual

- [ ] Criar tokens de cor para azul principal, azul escuro, azul claro, magenta, lima, texto, canvas e borda.
- [ ] Definir família sans-serif e escala tipográfica.
- [ ] Definir container central, largura máxima, gutters e escala de espaçamento.
- [ ] Padronizar bordas, raios e estados de foco.

### Componentes globais

- [ ] Cabeçalho utilitário + navegação principal.
- [ ] Logotipo e alinhamento responsivo.
- [ ] Botões primários e secundários.
- [ ] Links, badges, ícones, divisores e mensagens de apoio.
- [ ] Rodapé em colunas, redes sociais e áreas legais.

### Azul Viagens

- [ ] Hero de campanha com texto, CTA, setas e indicadores.
- [ ] Painel de busca sobreposto ao hero.
- [ ] Tabs por produto e subopções.
- [ ] Inputs de cidade, aeroporto, datas, passageiros, classe e bagagem.
- [ ] Cards compactos de destinos com duração, ícones e preço.
- [ ] Títulos de seção com traço magenta.
- [ ] Mosaico editorial de tiles fotográficos.
- [ ] Carrossel de ofertas com nome, localização e preço.
- [ ] Rodapé com suporte, parceiros, moeda e selos.

### Azul Fidelidade

- [ ] Hero emocional azul com pessoa e mensagem.
- [ ] Barra de atalhos com ícones.
- [ ] Módulo de consulta/descoberta em fundo azul com abas.
- [ ] Cards informativos em três colunas.
- [ ] Componente de passos numerados.
- [ ] Comparação de cinco níveis com progressão cromática.
- [ ] Faixas de ajuda contextual.
- [ ] Fileira de benefícios com ícones.
- [ ] Banners promocionais divididos entre texto e imagem.
- [ ] Grupos de logotipos por categoria.
- [ ] Faixas de suporte, links relacionados e rodapé denso.

### Qualidade

- [ ] Testar teclado, leitores de tela e contraste.
- [ ] Conferir legibilidade de metadados e preços.
- [ ] Testar layouts entre 320 px e desktop largo.
- [ ] Definir estados de loading, erro, foco, hover e disabled.
- [ ] Otimizar imagens e usar proporções consistentes.
- [ ] Verificar se grandes espaços verticais são intencionais, e não conteúdo ausente.

---

## 13. Observações e limitações

1. **As imagens não revelam a implementação interna.** Não é possível determinar framework, estrutura DOM, bibliotecas, breakpoints, animações ou tokens de CSS reais.
2. **Os valores de cor são aproximações.** Fotos, compressão e redimensionamento afetam a leitura dos pixels. Para fidelidade de marca, prefira cores oficiais ou valide os valores no site original.
3. **A primeira captura está em resolução visual baixa e largura pequena.** A estrutura e as famílias de componentes são identificáveis, mas parte do microtexto da página de fidelidade não é legível o suficiente para transcrição confiável.
4. **Não inferir responsividade a partir de uma captura desktop.** As recomendações responsivas neste documento são orientações para uma boa implementação, não afirmações sobre o funcionamento original.
5. **O foco deste arquivo é o sistema visual e os padrões de interface**, não a transcrição integral do texto comercial nem a validação de que todos os controles funcionam atualmente.

---

## Resumo executivo

A linguagem visual observada pode ser resumida em: **base branca e cinza-clara, identidade azul, fotografia aspiracional, CTAs cromaticamente destacados, cards organizados em grids/carrosséis e seções verticais com hierarquia simples**.

A Azul Viagens enfatiza descoberta e conversão: hero de campanha, formulário de busca sobreposto, preço em destaque e mosaico editorial. A Azul Fidelidade enfatiza entendimento e progressão: hero humano, atalhos, cards explicativos, níveis de categoria, benefícios, parceiros e suporte. Recriar as duas páginas de forma consistente exige compartilhar os tokens e componentes institucionais sem apagar as diferenças entre os objetivos de cada produto.
