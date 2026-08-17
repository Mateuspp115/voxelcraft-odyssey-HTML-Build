# Texture Engine v2 — arquitetura

## Pesquisa (resumo)
- Ruído procedural clássico (value/Perlin/fBm) continua sendo a base certa pra
  variação orgânica — confirmado pela literatura (fBm = várias oitavas de
  ruído em frequências/amplitudes diferentes somadas).
- Achado mais importante: **sombra boa não é `cor - X` matematicamente**.
  Pixel art feita à mão usa uma **paleta curada por material** (LUT: lookup
  table), indexada por "quanto de sombra" (0=luz, 1=escuro), com passo de
  matiz (hue shift) pra sombra/luz, não só escurecer/clarear em linha reta.
  Fonte: dev.to/jhmciberman (sistema de tilemap procedural com LUT de sombra
  por material) + prática padrão de pintura digital.
- Decisão sobre CDN: **não vou usar nenhuma lib externa de ruído**. O jogo já
  tem `hash3` determinística usada em todo o resto da geração de mundo (regra
  do projeto: nunca `Math.random()` em nada que precise ser igual pra todo
  jogador no multiplayer). Trocar por uma lib externa quebraria essa garantia
  ou exigiria seed manual idêntica — risco maior que o ganho.

## Camadas (pipeline por textura)
1. **base** — cor sólida de fundo
2. **shape** — ruído fBm (2-3 oitavas) definindo macro-variação/mancha
3. **shade** — indexa a paleta LUT do material usando o valor da camada shape
4. **detail** — elementos pequenos (flecks, pepitas, rachaduras) - por bloco
5. **cleanup** — quantização final (poucos tons discretos, "hand-painted")

## Paleta/LUT
Cada material tem uma paleta gerada automaticamente a partir da cor base via
HSL: desloca luminosidade E leve matiz (mais quente pra sombra, mais frio/
saturado pra luz) - não é só `L±X`.

## Qualidade
`TEX_QUALITY = 'low'|'medium'|'high'` controla: nº de oitavas do fBm, se a
camada detail roda, e nível de quantização do cleanup. Baixa qualidade =
menos oitavas + cleanup mais agressivo (mais rápido, ainda parece bem).

## Portabilidade
Módulo vive isolado (`@block:TextureEngineV2`), só depende de `hash3` (já
existe no projeto) e do Canvas2D padrão. Pra outro jogo: copiar o bloco +
implementar um adaptador de "receita por material" novo.
