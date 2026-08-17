# VoxelCraft Odyssey — CHECKPOINT v13-beta

> Ponto de restauração desta conversa. Se o ambiente resetar ou uma nova
> sessão precisar continuar, comece lendo isto inteiro antes de tocar em
> código. Arquivo de trabalho: `voxelcraft-odyssey_v13-beta.html`
> (377KB, 6689 linhas — v12 original tinha 310KB/5615 linhas).

## Estado geral
Base era v12. Nesta conversa: integrei o patch v6.7 de terceiros (com
adaptações), fechei a maior parte do checklist de 13 itens original,
construí um motor de textura procedural do zero (Texture Engine V2) e
corrigi vários bugs reais achados no caminho (não só os pedidos). Ainda NÃO
fiz bump formal pra v13 final — arquivo continua nomeado `v13-beta`
propositalmente até fechar os itens pendentes abaixo.

---

## ✅ Checklist original (13 itens) — status
1. Patch com texto errado — resolvido, patch de verdade foi enviado depois
2. Bug visual offline (Tailwind sem internet) — diagnóstico confirmado, sem ação
3. Permissão de câmera sob demanda — feito (JS + `MainActivity.java` da casca v5)
4. Bugs de spawn (água/lava/poço de mina) — feito
5. Config. Gerais x Config. do Mundo separadas — feito
6. Harness de preview de textura — feito, evoluiu pro motor completo (ver abaixo)
7. **Chat (reposição, global/proximidade, overlay) — PENDENTE**
8. **Iluminação de caverna (sky-exposure) — PENDENTE**
9. Fundo dos modais menos opaco + blur — feito
10. **Entradas naturais de caverna — PENDENTE**
11. Remover emojis (viraram SVG inline) — feito
12. Multiplayer: câmera travando, botão colar, cores — feito
13. Gamepad documentado no menu de ajuda — feito

## ✅ Casca Android
- **Use a v5**, não a v2 (v2 tinha CDN embutido incorretamente — contra a
  regra de manter CDN leve — e faltava a descoberta nativa de rede que o
  jogo já chama via `VoxelCraftAndroidBridge`).
- `MainActivity.java`: CAMERA saiu do pedido em lote do `onCreate`, agora é
  sob demanda via `requestCameraPermission()` (chamado só quando aperta
  ESCANEAR QR), resultado volta pro JS via `CustomEvent
  voxelcraft-camera-permission-result`.
- Validado por `javac` (sem SDK Android completo, mas confirma sintaxe —
  baseline de erros esperados vs. erros novos comparados antes/depois).

## ✅ Patch v6.7 (de terceiros, integrado com adaptação manual)
HardwareDetection (tier de GPU/RTX), LOD em duas camadas (32 blocos perto/96
longe), render distance configurável até 30, névoa/antialias ligáveis.
**Pulei de propósito** a parte de gamepad do patch — colidia com o
`GamepadInput` que já existia e funcionava (patch teria causado erro de
identificador duplicado).

---

## ✅ Texture Engine V2 — arquitetura (a parte grande desta conversa)

### Pipeline por textura
`base sólida → forma (fBm) → sombra (paleta + dithering) → detalhe
(específico do material) → opacidade (se o material precisar, ex. água)`

### Peças centrais (todas dentro do bloco `@block:TextureEngineV2`)
- **`hash3`**: hash determinística que já existia no jogo, usada em tudo
  (nunca `Math.random()` — regra do projeto, precisa bater entre jogadores).
- **`smoothNoise`/`fbm`**: ruído suave interpolado (bilinear+smoothstep),
  fBm soma várias oitavas. Existe em 2 versões: normal e **tileable**
  (`tileableSmoothNoise`/`tileableFbm` — usa módulo na grade de amostragem,
  garante que a borda direita bata exata com a esquerda). Use `tileable`
  pra qualquer material visto em grandes áreas contínuas (água, lava).
- **`makePalette(hex, steps)`**: gera paleta de N cores a partir de 1 cor
  base via HSL, deslocando luminosidade E matiz (mais quente na sombra,
  mais frio na luz) — não é `cor±X` linear.
- **`shadeFromPalette(palette, t, x, y)`**: **dithering ordenado (Bayer
  4x4)**, não interpolação contínua. Escolhe entre as 2 cores mais próximas
  da paleta baseado numa matriz de limiar por posição de pixel. Precisa de
  x,y sempre. Essa foi uma correção importante — a versão antiga
  interpolava cor continuamente (parecia foto borrada) e depois um
  `pixelCleanup` quantizava R/G/B independentemente (podia gerar cor fora
  da paleta, ex. pixel quase-branco por engano). **`pixelCleanup` foi
  removido** — dithering já resolve sem esse bug.
- **`TEV2_RECIPES`**: objeto com uma entrada por material. Campos:
  `baseColor(def)`, `shapeCell`, `shadeAmount`, `detail(ctx,palette,def,seed,q,variantIndex)`,
  `detailAlwaysOn`, `variants` (nº de variantes de posição, opcional),
  `tileable` (opcional), `opacity` (opcional, 0-1).
- **`generate(recipe, def, seed, variantIndex)`**: roda o pipeline inteiro.

### Sistemas extra construídos
- **Textura conectada (tipo OptiFine)**: só vidro por enquanto. 16 variantes
  (bitmask de 4 bits: bit0=cima,bit1=direita,bit2=baixo,bit3=esquerda,
  convenção documentada em `drawGlassVariant`/`addCubeFaces`). Direção
  "cima/direita" é calculada a partir dos PRÓPRIOS vértices da face (não
  tabela fixa por orientação) — evita ter que acertar de cabeça a
  convenção de flip de cada uma das 6 direções.
- **Variante de posição** (resolve flor repetindo igual em todo bloco):
  receita declara `variants: N`; `addCubeFaces` escolhe qual variante usar
  por bloco via hash determinística da posição no mundo (não regenera
  textura, só escolhe entre N versões pré-prontas). Reaproveitável pra
  qualquer bloco futuro que precise disso (cristal ocasional, rachadura
  variável, etc) — só declarar `variants` na receita.
- **Atlas com gutter/padding** (`ATLAS_PAD`, `ATLAS_CELL`): evita
  sangramento de mipmap entre células vizinhas do atlas — bug real que
  causava linha cinza entre blocos vizinhos (achado depois de ligar
  mipmap pra resolver chuvisco a distância).
- **Mipmap ligado**: `NearestFilter` de perto (visual pixel-art nítido),
  `NearestMipmapLinearFilter` de longe (sem chuvisco).

### Migrados pro motor v2 (13 de ~42 patterns totais)
`grass_top, dirt, stone, cobblestone, planks, log_ring, sand, lava, water,
grass_side, snow_grass_side, deep_stone, deep_cobblestone`

**Pendente**: os ~29 patterns restantes ainda usam o `TextureGenerator`
antigo (switch-case com `noisy()`) — dispatch em `draw()` checa
`TEV2_RECIPES[pattern]` primeiro, cai no antigo se não achar. Migrar aos
poucos, testando cada um (não precisa fazer tudo de uma vez).

**Checklist pra receita nova** (pedido do usuário, "padrão mestre"):
cor sempre de `colorTop/Side/Bottom` do bloco (nunca inventada, a menos que
o material não tenha cor natural, tipo lava/água); `tileable:true`
obrigatório pra material visto em área contínua grande; paleta sempre via
`makePalette`, nunca cor solta dentro de `detail()`.

---

## ✅ Geração de mundo

### Minério — distribuição triangular (pesquisado: geologia real + Minecraft 1.18+)
`ORE_RULES` agora usa `{peakY, halfWidth, peakChance}` em vez de chance
uniforme num intervalo. Checagem do mais raro pro mais comum (esmeralda
primeiro, carvão por último) — minério raro não perde o próprio pico pra
sobreposição de um comum. Mapa completo em `MAPA_MINERIOS.md` (já
entregue). Validado por simulação estatística antes de fechar.

### Lava
`lavaChanceAtY(y)` — probabilística, não mais corte binário. Quase certa
no fundo (Y≤5), cai suave, mantém piso pequeno (~1,5-2,5%) mesmo mais alto
(bolsão raro é geologicamente plausível).

### Pedra profunda
`deep_stone`/`deep_cobblestone` — inspirado no deepslate do Minecraft, sem
copiar (paleta roxo-acinzentada própria). Zona de transição gradual Y8-14
(`isDeepStoneAt`), não corte seco.

### CHUNK_HEIGHT (mundo tem só 64 blocos de altura)
**Não alterado** — anotado como pendência, mexe em quase todo o pipeline
(chunk/save/render), risco alto fazer junto com outras coisas. Fica pra
rodada própria e focada.

---

## 🐛 Bugs achados e corrigidos no caminho (não pedidos originalmente)
- `TextureGenerator.adjust()` gerava hex quebrado tipo `#7d.47feb...`
  sempre que o ajuste de cor era fracionário (quase sempre) — silenciava o
  ruído de quase toda textura procedural do jogo. Fix: `Math.round()`.
- Mipmap sem gutter sangrando cor de bloco vizinho no atlas.
- Borda escura universal (`rgba(0,0,0,0.16)` no canto de toda textura)
  criava grid visível entre blocos do mesmo tipo lado a lado. Removida.
- Variável `worldSeed` inexistente usada por engano no fix da lava — teria
  quebrado geração de caverna inteira (`ReferenceError`). Corrigido pra
  `seed` (parâmetro certo).
- `pixelCleanup` antigo quantizava R/G/B independentemente — podia gerar
  cor fora da paleta do material (pixel quase-branco do nada). Resolvido
  substituindo por dithering (ver Texture Engine V2 acima).
- Fila de carregamento de chunk processava em ordem de inserção do loop
  dx/dz (canto mais distante primeiro), não por distância real ao jogador.
  Corrigido: ordena por distância antes de processar.

---

## Decisões importantes (pra não repetir a mesma discussão)
- **Sem CDN externo no motor de textura** — teria que ter seed manual
  idêntica ao `hash3` existente pra não quebrar determinismo multiplayer;
  risco maior que o ganho.
- **Não consigo renderizar o jogo de verdade** (sem Chromium/Firefox
  funcionais neste ambiente, sem acesso de rede aos binários) — validação
  visual é via harness Node + Canvas2D isolado (testa geração de textura
  pixel a pixel, não o resultado 3D final com luz/câmera).
- **Não replico imagem de referência pixel a pixel** — nem a de terceiro
  nem a gerada por IA do próprio usuário — uso como guia de estilo/técnica,
  nunca cópia literal.

## Arquivos já entregues nesta conversa (referência)
`ARQUITETURA_TEXTURE_ENGINE.md`, `MAPA_MINERIOS.md`, `LISTA_PENDENCIAS.md`,
e múltiplos `voxelcraft-odyssey_v13-beta.html` (sempre o mais recente
substitui o anterior).
