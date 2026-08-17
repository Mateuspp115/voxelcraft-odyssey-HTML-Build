# Motor de Texturas do VoxelCraft Odyssey — Referência Técnica

> Não existia um README separado para o projeto (é um único arquivo HTML). Este documento existe só pra explicar o **motor de texturas** — como ele funciona por dentro, onde cada parte mora no arquivo, e todas as APIs disponíveis pra quem for programar um bloco novo ou mexer no motor em si. Escrito na v14.

---

## 1. Onde o motor mora no arquivo

O jogo inteiro é um `.html` só, organizado em `<script>` tags marcadas com comentários `/* @block:Nome:start */` / `/* @block:Nome:end */`. O motor de texturas está espalhado em 3 desses blocos, nesta ordem:

| Bloco | O que tem lá |
|---|---|
| `TextureGenerator` (parte 1) | `TEX_SIZE`, `sc()`, e o sistema **antigo** de desenho por `switch/case` (ver seção 11) |
| `TextureEngineV2` | O motor novo: paleta, dithering, ruído, pipeline `paint()`/`generate()`, `TEV2_RECIPES` (as receitas), API de qualidade gráfica, API de conexão de blocos |
| `TextureGenerator` (parte 2) | `TextureGenerator.draw()` (o despachante que decide V2 ou antigo), `drawGlassVariant`, `drawConnectVariant`, `drawFamilyVariant`, `iconCanvas` |
| `TextureAtlas` | Constrói o atlas (a imagem grande com todas as texturas coladas), aloca colunas extras, funções `getUVs*` que a malha 3D usa pra saber que pedaço do atlas mostrar em cada face |

Fora desses blocos, quem **usa** o motor:
- `BlockDefs` (bloco `BlockRegistry`) — cada bloco declara `pattern:{top,side,bottom}` apontando pro nome de uma receita.
- `addCubeFaces()` (dentro da classe do mundo, bloco de geração de malha) — decide, pra cada face de cada bloco no mundo, qual UV do atlas usar (inclui a lógica de bitmask de conexão).

---

## 2. Conceitos fundamentais

### 2.1 Determinismo (`hash3`)

Nada no motor usa `Math.random()`. Toda "aleatoriedade" vem de uma função hash determinística:

```js
function hash3(seed, x, y, z) {
  let h = (seed ^ 0x9e3779b9) | 0;
  h = Math.imul(h ^ x, 0x85ebca6b);
  h = Math.imul(h ^ y, 0xc2b2ae35);
  h = Math.imul(h ^ z, 0x27d4eb2f);
  h ^= h >>> 15; h = Math.imul(h, 0x735a2d97); h ^= h >>> 13;
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}
```

Entrada: 4 inteiros (`seed,x,y,z`). Saída: float determinístico em `[0,1)`. Mesmo input = mesmo output, sempre, em qualquer celular. É por isso que o mundo fica igual pra todo jogador sem precisar transmitir a textura pela rede — cada cliente gera a mesma coisa localmente a partir da mesma seed.

`seed` normalmente é `def.id*97 + (faceIndex+1)*131` — cada bloco e cada face tem uma seed própria, então blocos diferentes não parecem cópia um do outro.

### 2.2 Espaço de coordenadas (`TEX_SIZE` / `sc()`)

```js
let TEX_SIZE = 32;        // pixels por face de textura (muda com qualidade, ver seção 8)
let _TEX_SC  = TEX_SIZE/16;
function sc(v) { return Math.round(v * _TEX_SC); }
```

Todas as receitas são escritas pensando num espaço de **16 unidades**, nunca em pixels crus de `TEX_SIZE`. Quando uma receita precisa de um tamanho/posição, chama `sc(valor)`. Isso é o que permite a textura MUDAR de resolução (16px/32px/64px) sem reescrever nenhuma receita — o desenho todo escala junto.

Regra importante: ruído/grão fica em tamanho **absoluto** de pixel (não passa por `sc()`), de propósito — resolução maior deve trazer detalhe novo de verdade, não só esticar a imagem borrada.

---

## 3. Pipeline de geração — `paint()` / `generate()`

Toda receita passa pelo mesmo pipeline de 4 passos, implementado em `TextureEngineV2.paint(recipe, def, seed, variantIndex)`:

```
1. cor base sólida  →  2. forma (fBm)  →  3. sombreado (paleta + dithering)  →  4. detail()  →  5. opacidade (se aplicável)
```

**Passo a passo:**

1. `baseHex = recipe.baseColor(def)` — a receita devolve a cor "crua" do material (normalmente `def.colorTop`/`colorSide`).
2. `palette = makePalette(baseHex, q.paletteSteps)` — gera uma rampa de N tons a partir da cor base (ver seção 4).
3. Para cada pixel `(x,y)`:
   - `shape = fbm(seed, x, y, q.octaves, recipe.shapeCell)` → devolve um valor `[0,1)` de ruído orgânico multi-escala.
   - `t = 0.5 + (shape-0.5) * recipe.shadeAmount` → controla o quanto o ruído afeta o tom final (0 = plano, 1 = variação total).
   - pixel recebe `shadeFromPalette(palette, t, x, y)` (dithering, ver seção 4).
4. Se `q.detail` estiver ligado (ou `recipe.detailAlwaysOn===true`), chama `recipe.detail(ctx, palette, def, seed, q, variantIndex)` — aqui entram detalhes discretos (flor, veio de pedra, faísca de TNT etc.), desenhados por cima do sombreado de base.
5. Se `recipe.opacity < 1`, aplica alpha uniforme em tudo que não é transparente de verdade.

`generate()` é só `paint(...).canvas` — existe pra quem só quer o canvas pronto (as 16 receitas normais e o atlas usam essa). `paint()` devolve `{canvas, ctx, palette}` — usado pela API de conexão de blocos, que precisa da MESMA paleta pra pintar borda/variante com cor combinando.

---

## 4. Sistema de paleta e dithering

### 4.1 `makePalette(baseHex, steps)`

Gera uma rampa de `steps` tons a partir de 1 cor, deslocando **luminosidade E matiz** (não só escurece/clareia em linha reta — sombra fica mais quente, luz mais fria/saturada, que é como pintura de verdade funciona):

```js
for i em [0, steps):
  t = i / (steps-1)
  novaLuminosidade = clamp(L + (t-0.5)*0.55, 0.04, 0.96)
  novoMatiz        = (H + (0.5-t)*0.02 + 1) % 1
  novaSaturação    = clamp(S + (t<0.5 ? 0.08 : -0.05), 0, 1)
```

### 4.2 `shadeFromPalette(palette, t, x, y)` — dithering Bayer 4×4

```js
const BAYER_4X4 = [[0,8,2,10],[12,4,14,6],[3,11,1,9],[15,7,13,5]];
```

Dado um valor contínuo `t`, escolhe entre os DOIS tons de paleta mais próximos (nunca mistura cor — pixel sempre é uma cor exata da paleta):

```
idx = t * (steps-1)
i0 = floor(idx), i1 = min(steps-1, i0+1)
frac = idx - i0
threshold = (BAYER_4X4[y&3][x&3] + 0.5) / 16
resultado = frac > threshold ? palette[i1] : palette[i0]
```

Isso é a técnica clássica de dithering ordenado (mesma usada em pixel art profissional/jogos retrô tipo Return of the Obra Dinn) — dá a ILUSÃO de mais tons do que a paleta realmente tem, sem nunca borrar/misturar cor.

### 4.3 Quantos tons usar (`paletteSteps`)

Testado visualmente nesta sessão (comparação em `/mnt/user-data/outputs`, ver checkpoint): com **7 tons** (valor antigo) o dithering alterna entre cores diferentes demais → dá pra ver um "xadrez" (banding). Suave demais (40+ tons) começa a ficar homogêneo/liso, perdendo a textura granulada. **16-18 tons é o ponto ideal.** Valores atuais por qualidade: ver tabela da seção 8.

---

## 5. Ruído — `smoothNoise` / `fbm` / versões tileable

### 5.1 `smoothNoise(seedOffset, x, y, cellSize)` — value noise 2D

Ruído de valor com interpolação suave (smoothstep), NÃO Perlin gradiente (mais barato, resultado parecido pro que esse motor precisa):

```
gx = x/cellSize, gy = y/cellSize
x0 = floor(gx), y0 = floor(gy), fx = gx-x0, fy = gy-y0
v00,v10,v01,v11 = hash3 dos 4 cantos da célula
sx = fx²(3-2fx), sy = fy²(3-2fy)     // smoothstep, não interpolação linear
a = lerp(v00,v10,sx), b = lerp(v01,v11,sx)
resultado = lerp(a,b,sy)
```

### 5.2 `fbm(seedOffset, x, y, octaves, baseCell)` — Fractal Brownian Motion

Soma `octaves` camadas de `smoothNoise` em frequência crescente e amplitude decrescente (cada oitava tem metade da amplitude e metade do tamanho de célula da anterior):

```
amp=0.5, cell=baseCell
para cada oitava: soma += smoothNoise(seed+oitava*191, x,y,cell)*amp
                   amp *= 0.5;  cell = max(1, cell/2)
resultado = soma / somaDosAmp   // normalizado pra ficar em [0,1)
```

Isso dá variação orgânica em múltiplas escalas de uma vez (mancha grande + textura média + grão fino), técnica padrão de textura procedural.

### 5.3 Versões *tileable* (`tileableSmoothNoise` / `tileableFbm`)

Mesma matemática, mas a grade de amostragem **dá a volta** (`% cellsPerSide`) em vez de continuar reto — a borda direita do tile sempre bate exatamente com o valor que a esquerda teria. Usado por receitas com `tileable:true` (ex. `water`) — o motivo é que TODO bloco de água no mundo usa a MESMA textura estática, então só fica "sem costura" se a própria textura já nascer repetível (diferente da técnica de conexão por vizinhança, que esconde a borda dependendo de quem está do lado).

---

## 6. `TEV2_RECIPES` — o contrato de uma receita

Cada entrada em `TEV2_RECIPES` é um objeto com estes campos (só `baseColor` é obrigatório):

| Campo | Tipo | Obrigatório | O que faz |
|---|---|---|---|
| `baseColor` | `(def) => hexString` | **sim** | Cor crua do material. Sempre ler de `def.colorTop`/`colorSide`/`colorBottom` — nunca cor inventada, a não ser que o material realmente não tenha cor natural (ex. cinza do cobblestone). |
| `shapeCell` | number | não (default 8) | Tamanho de célula do ruído de base — controla o tamanho das "manchas" da forma. Maior = manchas maiores. |
| `shadeAmount` | 0–1 | não (default 0.9) | Quanto o ruído de forma afeta o tom (0=chapado, 1=variação máxima). |
| `detail` | `(ctx,palette,def,seed,q,variantIndex) => void` | não | Desenha detalhes discretos por cima (flor, veio, faísca...). Só roda se `q.detail` estiver ligado OU `detailAlwaysOn:true`. |
| `detailAlwaysOn` | boolean | não | Força `detail()` a rodar mesmo em qualidade baixa (`q.detail:false`) — usar só quando o detalhe é ESSENCIAL pra identidade visual do bloco (ex. franja de grama), não pra enfeite opcional. |
| `variants` | integer | não | Nº de variantes de **posição** (não confundir com conexão) — ex. grama com/sem flor. Escolhida deterministicamente pela posição do bloco no mundo, não pelos vizinhos. |
| `opacity` | 0–1 | não | Alpha uniforme aplicado no fim (fluidos como água/lava). |
| `tileable` | boolean | não | Usa `tileableFbm` em vez de `fbm` — textura nasce sem costura quando repetida (ver 5.3). |
| `connect` | objeto | não | Ativa a API de conexão de blocos — ver seção 9. |

### Exemplo mínimo

```js
meu_bloco_novo: {
  baseColor: (def) => def.colorTop || '#888888',
  shapeCell: 8, shadeAmount: 0.6,
  detail(ctx, palette, def, seed) {
    // desenhar algo em cima, opcional
  }
}
```

Isso sozinho já dá: paleta correta, dithering, ruído orgânico, tudo escalando com qualidade gráfica — sem escrever NADA disso na mão.

---

## 7. Ainda não migrados pro V2 — como migrar um

16 receitas estão em `TEV2_RECIPES` hoje: `grass_top, dirt, stone, cobblestone, deep_stone, deep_cobblestone, planks, log_ring, sand, log_side, tnt_top, lava, water, grass_side, grass_side_lush, snow_grass_side`. As outras (~26 patterns) ainda estão no sistema antigo (`TextureGenerator.draw`, `switch/case`, ver seção 11).

**Passo a passo pra migrar um pattern:**
1. Achar o `case 'nome_do_pattern':` no switch antigo (dentro de `TextureGenerator.draw`) — serve de referência do visual atual, mas **não apagar** (o dispatcher já ignora automaticamente, vira código morto sem custo).
2. Criar a entrada equivalente em `TEV2_RECIPES` (seção 6).
3. Testar via harness Node isolado (ver seção 13) ANTES de considerar pronto — texturas pequenas (~5-8px de forma) sofrem muito com escala errada, testar economiza retrabalho.
4. `draw()` já prioriza `TEV2_RECIPES` automaticamente — não precisa mexer no dispatcher.

---

## 8. API de qualidade gráfica

Ponto de entrada único: **`TextureEngineV2.setQuality('low'|'medium'|'high')`**. Já está ligado ao seletor "Baixa/Média/Alta" que existe no menu de configurações (`applyQualityPreset()`, bloco `GameBootstrap`) — trocar ali já reconstrói o atlas inteiro com os valores novos, nenhum bloco precisa saber que isso aconteceu.

| Nível | `res` (TEX_SIZE) | `octaves` | `detail` | `paletteSteps` | `cleanupLevels` |
|---|---|---|---|---|---|
| `low` | 16px | 1 | desligado | 12 | 10 |
| `medium` (padrão) | 32px | 2 | ligado | 18 | 16 |
| `high` | 64px | 3 | ligado | 28 | 24 |

- **`res`**: tamanho real da textura gerada. Baixa qualidade não é só "textura mais feia" — é literalmente metade do tamanho, atlas mais leve, menos VRAM, build mais rápido (importante pro Moto G35).
- **`octaves`**: quantas camadas de ruído fBm somar (seção 5.2). Menos oitavas = mais barato, forma mais simples.
- **`detail`**: liga/desliga a chamada de `recipe.detail()` pros patterns que não marcaram `detailAlwaysOn`.
- **`paletteSteps`**: tons na paleta (seção 4.3).

**Funções internas (não chamar direto, exceto se for mexer no motor):**
- `applyTextureQuality(tier)` — worker que `setQuality` chama; muda `TEX_QUALITY`, `TEX_SIZE`, e reconstrói o atlas.
- `setTextureResolution(newSize)` — muda só `TEX_SIZE`/`_TEX_SC`.
- `updateAtlasCellSize()` — recalcula `ATLAS_PAD`/`ATLAS_CELL` depois que `TEX_SIZE` muda.

---

## 9. API de conexão de blocos

Duas formas — nenhuma delas exige escrever lógica de bitmask/atlas na mão, o motor cuida disso sozinho a partir de UMA declaração `connect` na receita.

### 9.1 `mode: 'self'` — conecta com o MESMO bloco (estilo vidro)

```js
minha_receita: {
  baseColor: (def) => def.colorTop,
  // ... resto normal ...
  connect: {
    mode: 'self',
    // chamada DEPOIS do corpo normal já pintado. `edges` diz em quais
    // lados NÃO tem vizinho igual (então: pode/deve desenhar borda ali).
    border(ctx, palette, def, seed, edges) {
      // edges = {up, right, down, left, bitmask}
      if (edges.up)    { /* desenha traço no topo */ }
      if (edges.right) { /* desenha traço na direita */ }
      // etc.
    }
  }
}
```

O motor gera as **16 variantes** sozinho (2⁴ combinações de vizinho em cada lado) e reserva 16 colunas no atlas automaticamente (`TextureAtlas.selfConnectCols`). Em tempo de malha (`addCubeFaces`), calcula o bitmask certo olhando os 4 vizinhos de borda da face (usando a orientação real da face no mundo, funciona pra qualquer uma das 6 direções sem tabela fixa) e escolhe a textura certa.

> O vidro (`glassId`) usa um caminho **dedicado** mais antigo (`drawGlassVariant`/`getUVsVariant`), que continua intocado — funciona, testado, sem motivo pra arriscar regressão. A API genérica acima é o caminho pros PRÓXIMOS blocos autoconectáveis (grades, cercas etc.) — mesma técnica, sem duplicar código.

### 9.2 `mode: 'family'` — conecta com blocos de OUTRO tipo mas do mesmo "estilo" (estilo grama+terra)

```js
grass_side: {
  // ... resto normal ...
  connect: {
    mode: 'family',
    family: ['grass_top', 'grass_side'],  // patterns que contam como "parente"
    threshold: 2,                          // quantos dos 4 vizinhos de borda precisa
    variant: 'grass_side_lush'             // receita alternativa a usar quando bate o threshold
  }
}
```

O motor conta quantos dos 4 vizinhos de borda pertencem à família declarada (checando se QUALQUER face do bloco vizinho usa um pattern da lista) e, se bater o `threshold`, troca pra textura da receita em `variant` — que é uma receita comum, sem saber nada sobre conexão. Só precisa existir 1 coluna extra no atlas por pattern family-connect (`TextureAtlas.familyConnectCols`), bem mais barato que o modo self (que precisa de 16).

**Exemplo já implementado:** `grass_side` perto de 2+ blocos de grama vira `grass_side_lush` (cobertura verde quase total, em vez da franja curta padrão) — dá sensação de grama densa/crescida quando há vários blocos de grama juntos.

### 9.3 Resumo de quando usar qual

- **self**: o bloco só "sabe" conectar com uma cópia EXATA de si mesmo (vidro, futuramente grades/cercas).
- **family**: blocos DIFERENTES que pertencem ao mesmo conceito visual (grama com grama vizinha, terra perto de grama, etc.) — mais barato, sem bitmask.

---

## 10. `TextureAtlas` — como o atlas é montado

O atlas é 1 canvas grande: `totalCols × 3 linhas` (linha 0=top, 1=side, 2=bottom), cada célula com `ATLAS_PAD` de gutter (margem) pra não vazar cor no mipmap.

Alocação de colunas, nesta ordem:
1. **1 coluna por bloco** (`BlockKeys.length`) — a textura normal top/side/bottom de cada bloco.
2. **+16 colunas** se existir vidro (`glassId`) — variantes de conexão do vidro (caminho dedicado).
3. **+N colunas** por pattern com `variants>1` (variante de posição, ex. flor da grama).
4. **+16 colunas** por pattern com `connect:{mode:'self'}` (novo, genérico).
5. **+1 coluna** por pattern com `connect:{mode:'family'}` (a textura "conectada").

Funções de leitura de UV (todas devolvem `[u0,v0,u1,v0,u1,v1,u0,v1]`, 4 pares uv por face):
- `getUVs(blockId, face)` — caminho padrão.
- `getUVsVariant(face, bitmask)` — vidro (dedicado).
- `getUVsPositionVariant(pattern, face, variantIndex)` — variante de posição.
- `getUVsConnectVariant(pattern, face, bitmask)` — self-connect genérico.
- `getUVsFamilyVariant(pattern, face)` — family-connect.

`TextureAtlas.rebuild()` reconstrói tudo com o estado atual (chamado depois de trocar qualidade gráfica ou depois de um mod registrar bloco novo) — reaproveita o MESMO objeto de textura do Three.js, então tudo que já está desenhado no mundo atualiza sozinho.

---

## 11. Sistema antigo (`TextureGenerator.draw`, switch/case)

Ainda ativo pros ~26 patterns não migrados. `draw(pattern, color, def, faceIndex)` primeiro checa `TEV2_RECIPES[pattern]` — se existir, usa o motor novo; senão cai no `switch(pattern)` antigo, que termina sempre com `this.pixelCleanup(ctx, 18)` (quantização simples por canal, 18 níveis fixos — mais simples que o dithering por paleta do V2, é o que dá aquele visual ligeiramente diferente entre um pattern migrado e um que não é).

Não é urgente migrar tudo de uma vez — convenção do projeto é migração gradual, testando um de cada vez.

---

## 12. Como adicionar um bloco novo do zero

1. Definir em `BlockDefs`: `pattern:{top,side,bottom}` apontando pro nome de uma receita (existente ou nova) + `colorTop/colorSide/colorBottom`.
2. Se a receita não existir ainda, criar em `TEV2_RECIPES` (seção 6) — nunca no switch antigo (esse é só legado).
3. (Opcional) Declarar `connect` se o bloco deve se conectar visualmente com vizinhos (seção 9).
4. (Opcional) Declarar `variants` se precisar de variação visual por posição (tipo flor).
5. Testar no harness Node (seção 13) antes de considerar pronto.
6. Nada mais — o atlas, o dithering, a escala por qualidade gráfica, tudo automático.

---

## 13. Como testar uma receita sem abrir o jogo (harness Node)

O motor de textura (`TEX_SIZE`, `sc`, `hash3`, `TextureEngineV2`, `TEV2_RECIPES`) não depende de DOM real — só de um Canvas2D. Pra testar isolado:

1. Extrair o trecho entre `/* @block:TextureEngineV2:start */` e `:end` + a função `hash3` pro mesmo arquivo `.js`.
2. Substituir `document.createElement('canvas')` por um Canvas2D fake (mínimo: `fillRect`, `arc`+`fill`, `stroke`, `getImageData`/`putImageData`) ou pela lib `canvas` do npm se disponível.
3. Chamar `TextureEngineV2.generate(TEV2_RECIPES.nome, defFalso, seed, 1)`, pegar os pixels e salvar como PNG (encoder mínimo com `zlib.deflateSync` + chunks manuais funciona sem nenhuma dependência).
4. Ampliar o PNG resultante (nearest-neighbor) pra inspecionar — 32×32 real é ilegível em tamanho normal.

Isso foi usado nesta sessão pra validar `tnt_top`, `log_side`, a variação de paleta e a variação de resolução ANTES de considerar qualquer coisa pronta — pegou pelo menos 2 bugs (um na receita, um no próprio harness de teste) que só apareceriam jogando de verdade, bem mais devagar de depurar lá.

---

## 14. Limitações conhecidas / não implementado ainda

- **Conexão self genérica**: motor pronto e testado (geração de textura), mas sem nenhum bloco do jogo usando ainda além do vidro (que usa o caminho dedicado antigo) — falta um bloco candidato real (grade, cerca) pra ser o primeiro caso de uso de verdade.
- **Family-connect**: só `grass_side`↔`grass_side_lush` implementado. O mesmo mecanismo serve pra qualquer outra dupla (ex. neve encostando em neve, areia virando duna perto de mais areia) — é só declarar.
- **Sistema antigo (26 patterns)**: continua sem dithering por paleta fina, sem tileable, sem API de conexão — herda só a resolução dinâmica (`TEX_SIZE`) e o `pixelCleanup` próprio dele.
- **`connect` com mais de 1 face por bloco**: hoje testado só em patterns usados no `side`. Não deveria ter problema em `top`/`bottom` (a mesma lógica de vértices já é orientação-agnóstica, usada assim no vidro), mas ainda não foi testado nessa combinação.
- **Traits/helpers compartilhados entre receitas**: só existe 1 por enquanto (`paintGrassFringe`, usado por `grass_side`/`grass_side_lush`). A ideia de "motor separado dos blocos por completo" (helpers tipo `woodGrain()`, `granular()`, `crystalline()` reutilizáveis por várias receitas de uma vez) ainda não foi generalizada — é o próximo passo natural se mais receitas repetirem padrão parecido.

---

## 15. Números de referência rápida

| Constante | Valor |
|---|---|
| `TEX_SIZE` (padrão, qualidade média) | 32px |
| `_TEX_SC` | `TEX_SIZE/16` (1 em baixa-8px-equiv., 2 em média, 4 em alta) |
| `ATLAS_PAD` | `max(2, sc(2))` |
| `ATLAS_CELL` | `TEX_SIZE + ATLAS_PAD*2` |
| Paleta (baixa/média/alta) | 12 / 18 / 28 tons |
| Oitavas de ruído (baixa/média/alta) | 1 / 2 / 3 |
| Receitas migradas pro V2 | 16 de ~42 patterns totais |
| Variantes self-connect | 16 (2⁴, 1 bit por lado: cima/direita/baixo/esquerda) |
| Matriz Bayer | 4×4, valores 0-15 |

---

*Documento gerado na v14, sessão de trabalho no motor de texturas. Atualizar sempre que a API do motor mudar — é fácil ficar desatualizado porque o motor evolui mais rápido que a documentação se ninguém atualizar junto.*
