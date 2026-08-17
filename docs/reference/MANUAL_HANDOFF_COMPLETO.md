# VoxelCraft: Odyssey — Manual de Handoff Completo

Documento gerado a partir de auditoria real do arquivo `voxelcraft.html`
(versão 6.5.0, 4176 linhas, 224 KB, 27 módulos nomeados). Todo número e
afirmação técnica aqui foi conferido rodando código de verdade contra o
HTML atual — não é um resumo de memória da conversa.

---

## 0. Regras inegociáveis do projeto (ler antes de qualquer coisa)

1. **Um único arquivo `.html`.** Todo o jogo — motor, texturas, sons,
   sistema de mods, sistema de atualização, multiplayer — vive dentro de
   um HTML só. Nenhuma dependência externa exceto CDNs de biblioteca
   (Three.js, Tailwind, JSZip) carregadas por `<script src>`.
2. **Roda em Android, Windows e navegador comum, sem servidor pago.**
   Multiplayer é P2P (WebRTC nativo). Mods e saves ficam no dispositivo
   (IndexedDB/localStorage). Nada disto depende de Firebase, Cloudflare,
   ou qualquer conta paga.
3. **Nunca regredir.** Toda mudança nova deve ser validada contra o que
   já existe antes de ser aceita — sintaxe, blocos pareados, referências
   cruzadas. Prática usada a conversa inteira: extrair o JS real do HTML
   final e rodar testes de verdade nele, nunca assumir que "deve
   funcionar".
4. **Texturas atuais (baseadas em CDN do Minecraft) são temporárias.**
   Usadas só para ter todos os blocos e mecânicas prontos mais rápido;
   serão substituídas por arte própria depois. Mecânicas de jogo devem
   ser criativas/próprias, não cópia 1:1 do Minecraft.
5. **Sem CDNs que exigem internet na primeira execução** (as 12
   bibliotecas tipo lil-gui/Yuka/socket.io mencionadas em uma mensagem
   antiga foram explicitamente descartadas por decisão do usuário).

---

## 1. Estado atual do jogo (v6.5.0) — o que existe de verdade

### 1.1 Motor e mundo
- Three.js r128, chunks de 16×64×16, geração por ruído Perlin 2D/3D
  **seedado e determinístico** (mesma seed = mesmo mundo sempre — testado
  explicitamente após um bug real onde árvores usavam `Math.random()`
  puro).
- 4 biomas (planície, floresta, deserto, neve), cavernas 3D, minérios por
  faixa de profundidade, árvores proceduralmente geradas.
- 54 blocos/itens definidos em `BlockDefs` (confirmado por contagem real).
- Raycast voxel via algoritmo DDA (Amanatides & Woo) para mirar/minerar/
  colocar blocos — testado com casos eixo-alinhado, diagonal, alcance
  máximo e posição de colocação.
- Horizonte distante (LOD) por heightmap simplificado, inspirado no mod
  Distant Horizons mas reimplementado do zero (técnica genérica, não
  código copiado).
- Física de jogador: pulo, sprint, voo (criativo), nado, dano de queda/
  lava/afogamento/cacto, fome, vida, respiração.
- Mobs passivos (vaca, ovelha, galinha, porco): nascem fora do campo de
  visão do jogador, com fade-in lento (5,5–8s), sem queda ao surgir,
  evitam lava e quedas, colidem com o jogador.
- Ciclo dia/noite com céu gradiente e estrelas.

### 1.2 Salvamento
- Multi-mundo real (cada mundo tem ID próprio, listagem, exclusão
  individual) — não é mais save único.
- `saveFormatVersion` no payload (adicionado nesta fase; saves antigos
  sem essa marca são tratados como versão 1 automaticamente).
- Mobs persistem entre sessões (bug real corrigido: antes, animais
  sumiam ao recarregar o mundo).
- Salvamento automático robusto: `beforeunload` **+** `visibilitychange`
  **+** `pagehide` juntos (corrige um bug real e documentado: `beforeunload`
  sozinho não é confiável em iOS Safari).
- Migração automática do formato antigo (single-save) para o novo
  formato multi-mundo, para não perder progresso de versões anteriores.

### 1.3 Interface
- Fluxo Título → Selecionar Mundo → Criar Mundo, estrutura conferida
  contra a wiki oficial do Minecraft (era 1.12.2), não copiada
  visualmente.
- Menu de Configurações reorganizado em 3 seções (Áudio e Controles,
  Vídeo, Jogo) com hierarquia visual.
- Sistema de diálogo próprio (`voxelAlert`/`voxelConfirm`) substituindo
  os 8 usos de `alert()`/`confirm()` nativos do navegador/WebView (que
  renderizavam com o estilo feio do sistema operacional).
- HUD com vida, fome, respiração, coordenadas, FPS, painel de depuração
  (F3).
- Controles touch completos (D-pad, botões de quebrar/colocar/pular/
  comer/voar), com `preventDefault` para não rolar a página.

### 1.4 Sistema de Mods (`.mcmod`)
- Pacote ZIP: `mod.json` + `codigo/` (JS **ou TypeScript**, transpilado
  no navegador) + `texturas/` + `sons/` + `data/`.
- Fica salvo no **IndexedDB** do navegador — nunca toca o arquivo HTML.
- Ativar/desativar/remover, escopo por mundo específico ou global, log
  de erro por mod.
- Lista de segurança: um mod não pode referenciar `parsePatch`,
  `VoxelCraftUpdater`, `ModStorage`, `TSTranspiler`, `eval(`, etc. —
  barreira entre "conteúdo de jogador" e "código do motor".

### 1.5 Sistema de Atualização (`.patch`)
- Ferramenta de **desenvolvedor**, separada dos Mods. ZIP com
  `manifest.patch` (JSON de comandos) + `scripts/` + `assets/`.
- O jogo inteiro é dividido em **27 blocos nomeados**
  (`/* @block:NOME:start/end */`), permitindo mirar, mover, renomear,
  copiar, ou substituir qualquer parte pelo nome, sem precisar saber
  número de linha.
- Comandos disponíveis: `ADD`, `REPLACE`, `REMOVE`, `MOVE`, `RENAME`,
  `COPY`, `MERGE`, `BACKUP`, `RESTORE`, `VERIFY`, `IF`/`ELSE`/`ENDIF`,
  `RUN`, `ENABLE`/`DISABLE`, `IMPORT`/`EXPORT`.
- **Detecção automática de conflito de nomes**: todo `ADD` verifica se o
  código novo declara uma função/classe/const que já existe no nível
  mais externo do arquivo (rastreando profundidade real de chaves, não
  regex ingênuo — corrigido depois de um falso-positivo real encontrado
  em teste). Recusa a atualização inteira se houver colisão, a não ser
  que `allowNameConflict: true` seja explicitado.
- Conversão automática de assets: PNG/JPG → textura comprimida (RLE por
  pixel com fallback), WAV/OGG/MP3 → PCM Int16 comprimido, GLSL → string,
  TTF/OTF → FontFace — tudo virando módulo JS textual inserido no HTML.
- Pipeline de validação antes de liberar: aplica em cópia → checa
  sintaxe → checa estrutura essencial → testa boot num iframe isolado.
- Pode **aplicar ao vivo na página atual, sem recarregar** (reexecuta os
  blocos `<script>` novos/alterados), além de gerar o `.html` completo
  para distribuir.

### 1.6 Multiplayer (P2P, sem servidor)
- `RTCPeerConnection` **nativo do navegador**, zero biblioteca externa.
- STUN público gratuito (Google) só para atravessar NAT — nenhum
  servidor de jogo, nenhuma conta paga.
- Sinalização (troca do "convite" inicial) é **manual**: código de 6
  caracteres + texto para copiar/colar em qualquer app de mensagem.
  Leitura por QR code **não foi implementada** (decisão consciente:
  geração de QR exige correção de erro Reed-Solomon não-trivial, não
  arriscado sem poder testar em navegador real).
- Host autoritativo para o mundo (blocos), cada peer autoritativo para a
  própria posição. Testado: host rejeita quebrar bloco já vazio e
  colocar em cima de bloco ocupado; peer que entra depois recebe
  histórico completo de edições.
- Lista de "amigos salvos" (nome + data da última conexão) — **não** é
  lista de presença online (isso exigiria servidor, que foi
  explicitamente descartado).
- Acessível de dentro do jogo via menu de pausa, sem precisar sair para
  o menu principal.

### 1.7 Cascas nativas (APK / EXE)
- **Rota Tauri (Rust)**: código-fonte completo (`main.rs`, `Cargo.toml`,
  `tauri.conf.json`) documentando esquema A/B de atualização
  (`install_update`, `revert_to_previous`, `cleanup_old_versions`,
  `restart_app`). **Não compilado** — trava em duas dependências:
  `crates.io` bloqueado por rede, e falta a stdlib Rust para Android
  (`rust-std-aarch64-linux-android`). Pedido de vendor já foi enviado ao
  usuário (`tauri_vendor_request.tar.xz`), resposta pendente.
- **Rota Android nativo (Java, sem Rust)**: alternativa criada quando a
  rota Tauri travou. `MainActivity.java` usando `android.webkit.WebView`
  puro, mesmo esquema A/B implementado em Java + `SharedPreferences`,
  tela cheia real via `sensorLandscape` (mesma técnica usada por
  Unity/Unreal, confirmado por fonte), ponte JS-Java
  (`VoxelCraftAndroidBridge`) com a mesma assinatura de método que o
  lado Tauri usa — o HTML não precisa saber qual casca está rodando.
  Script `build_apk.sh` orquestrando `aapt2`+`javac`+`d8`+`apksigner`.
  **APK não compilado ainda** — as ferramentas Android (SDK/NDK/aapt2)
  enviadas em rodadas anteriores não persistem entre sessões deste
  ambiente; precisam ser reenviadas para o build final rodar.
- **Reutilizável para outros jogos**: confirmado — trocar de jogo, ou
  aplicar uma atualização, significa só substituir
  `app/src/main/assets/index.html`. Nada no Java muda.
- **EXE (Windows)**: ainda não iniciado. Rota planejada: Tauri (quando
  resolver) ou WebView2 nativo do Windows via executável C#/.NET
  pequeno, no mesmo espírito da casca Android.

---

## 2. Arquitetura interna — os 27 blocos, em ordem real no arquivo

```
 1. BlockDefs           - definicao dos 54 blocos/itens
 2. BlockRegistry        - calcula IDs, lookups de solidez/transparencia
 3. TextureGenerator     - desenha texturas proceduralmente (16x16)
 4. TextureAtlas         - monta atlas de todas as faces de todos os blocos
 5. NoiseSystem          - ruido Perlin deterministico (seedado)
 6. WorldGenerator       - terreno, biomas, cavernas, minerios, arvores
 7. SoundFX              - sons sintetizados via WebAudio
 8. RaycastEngine        - raycast voxel DDA
 9. VoxelWorld           - chunks, malha, edicoes, luzes, save/load
10. SimpleAnimal         - mobs passivos
11. LODManager           - horizonte distante
12. PlayerCharacter      - fisica, vida/fome/respiracao, mineracao
13. SkyCycle             - dia/noite, ceu, estrelas
14. SaveSystem           - multi-mundo, versionamento, migracao
15. GameBootstrap        - inicializacao, loop principal, HUD
16. HooksAndAPI          - eventos extensiveis + window.VoxelCraft
17. ChangelogV61         - registro de changelog embutido (exemplo)
18. ModSystem            - runtime de Mods (.mcmod)
19. AssetRuntime         - registrador de texturas/sons convertidos
20. ConflictDetector     - detector de conflito de nomes para patches
21. UpdateSystem         - interpretador de .patch, conversores, plataforma
22. ModsUI               - interface da tela de Mods
23. UpdaterUI            - interface da tela de Atualizacoes
24. MultiplayerCodec     - codificacao de convite/sala
25. MultiplayerProtocol  - protocolo host/cliente
26. MultiplayerTransport - RTCPeerConnection real
27. MultiplayerUI        - interface da tela de Multiplayer
```

### API pública (`window.VoxelCraft`)

```javascript
window.VoxelCraft = {
  Hooks,                 // onSetBlock, onBreak, onChunkBuilt, onPlayerDamaged, onPlayerDeath, onFrame
  BlockDefs,
  getBlockKeys, getBlockById, getWorld, getPlayer, getScene,
  registerBlock(key, def),
  mods: { list, installMcmod, remove, setEnabled },
  updates: { process },
  version: '6.5.0'
};
```

### Plataforma (`window.VoxelCraftPlatform`)
Detecta automaticamente se está rodando em navegador comum, casca Tauri
(`window.__TAURI__`), ou casca Android nativa
(`window.VoxelCraftAndroidBridge`) — mesmo contrato de método
(`installUpdate`) nos três casos.

---

## 3. Dicas de edição usadas a conversa inteira (para manter na próxima)

1. **Nunca confiar sem testar.** Toda peça de lógica não-trivial (patch
   interpreter, codec de convite, protocolo multiplayer, geração de
   mundo) foi escrita e testada **isoladamente em Node** antes de entrar
   no HTML — e depois **revalidada extraindo o código exato do HTML
   final**, não uma cópia separada. Isso pegou bugs reais várias vezes
   (ver seção 4).
2. **Extrair e rodar `node --check` no JS de todo `<script>` inline**
   depois de qualquer edição, sem exceção.
3. **Validar pareamento de blocos** (`@block:NOME:start/end`) depois de
   qualquer edição estrutural — inversões de marcador já causaram bugs
   reais duas vezes nesta conversa.
4. **Cuidado com `</script>` como string literal** dentro de um bloco
   `<script>` real — o navegador (e o regex de extração) interpreta como
   fechamento de tag. Sempre escrever como `'<' + '/script>'` quando
   necessário referenciar isso em código.
5. **`Math.random()` é proibido em qualquer coisa que precise ser igual
   para todo mundo** (geração de mundo, textura). Usar `hash3`/ruído
   seedado. `Math.random()` só é aceitável em comportamento cosmético
   (variação de mob, pitch de som, timing de spawn).
6. **Regex simplificado para checar strings/comentários em Java ou JS dá
   falso positivo.** Usar um percorrimento caractere-a-caractere que
   trata escapes de verdade antes de confiar num "erro" de sintaxe.

---

## 4. Bugs reais encontrados e corrigidos nesta conversa (não regredir)

- Faces de topo/fundo de todo bloco com winding de vértices invertido
  (causava culling errado, "buracos" visuais).
- Ground-stickiness: jogador/animais repetiam o som de pouso
  indefinidamente ao ficar parados (fresta de ar entre bloco e pé).
- Mobs nasciam na frente do jogador, caindo, sem fade — corrigido para
  nascer fora do campo de visão, no chão certo, com fade lento.
- Canvas redimensionava com base em `window.innerWidth/Height`
  (instável em mobile) — trocado para `canvas.clientWidth/Height`.
- Árvores usavam `Math.random()` puro — mesma seed gerava florestas
  diferentes entre sessões. Corrigido para hash determinístico.
- Texturas (ruído de pedra/terra) também usavam `Math.random()` puro —
  mesmo bug de determinismo, mesma correção.
- `beforeunload` sozinho não salva de forma confiável em iOS Safari —
  adicionado `visibilitychange` + `pagehide`.
- Mobs não persistiam no save (somem ao recarregar) — corrigido.
- Save sem número de versão — adicionado `saveFormatVersion`.
- Sprint não consumia fome extra — pendente de correção (ver seção 5).
- `miningActive` não resetava ao mirar bedrock (desperdício de estado,
  sem impacto visual) — pendente de correção (ver seção 5).
- Acentuação ausente sistematicamente em nomes de blocos e textos de UI
  — corrigido nesta fase (menu), pode haver resíduos em texto adicionado
  depois.
- `ADD ... atEnd` no sistema de patch inseria código **depois de
  `</html>`**, fora de qualquer `<script>` — invisível ao `VERIFY` e
  ignorado silenciosamente pelo navegador. Corrigido para inserir antes
  do fechamento do último `<script>` real.
- Blocos remotos recebidos via multiplayer (`setBlockSilent`) não
  reconstruíam a malha visual — corrigido com `applyRemoteBlock`
  dedicado (dado + remesh).
- Dois casos de marcadores `@block:` invertidos (`:end` antes do
  `:start` seguinte) introduzidos por mim mesma durante edições —
  ambos encontrados só porque testei depois, não antes.
- 8 usos de `alert()`/`confirm()` nativos (visual feio do SO) —
  substituídos por diálogo customizado.

---

## 5. Checklist do que falta / bugs pendentes, com prioridade sugerida

### Prioridade alta (afeta jogabilidade ou risco de dado)
- [ ] **Sprint não consome fome extra** — confirmado real, ainda não
      corrigido.
- [ ] **`localStorage` pode se aproximar do limite de ~5MB** em sessões
      muito longas de construção massiva (testado: ~0,05MB em uso
      normal, ~2,6MB em cenário extremo de 500 chunks/500 mil edições).
      Não é falha imediata, mas vale migrar edições de mundo para
      IndexedDB (mesmo mecanismo já usado pelos Mods) antes que vire
      problema real.
- [ ] **Compilar o APK de verdade.** Duas rotas em paralelo, nenhuma
      finalizada: (a) Tauri — aguardando vendor do Cargo + stdlib
      Android; (b) Android nativo Java — aguardando reenvio das
      ferramentas SDK/NDK/aapt2/d8/apksigner (não persistem entre
      sessões deste ambiente).
- [ ] **Gerar o EXE (Windows)** — não iniciado.

### Prioridade média (qualidade/robustez)
- [ ] `miningActive` não reseta ao mirar bedrock (limpar estado, sem
      impacto visual atual).
- [ ] Point lights (tocha, pedra luminosa) vazam luz através de paredes
      — teria que ativar sombra por point light, com custo de
      performance a avaliar antes de decidir a abordagem.
- [ ] Fornalha usa a mesma textura em todas as faces laterais (sem face
      "de trás" diferente) — puramente estético.
- [ ] `AudioContext` já retoma no gesto do usuário e a casca Android
      nativa já reforça isso via `onResume`, mas o caminho "navegador
      solto" (fora de qualquer casca) ainda não tem um listener de
      `visibilitychange` chamando `resume()` de volta.
- [ ] QR code para conexão multiplayer — adiado conscientemente, exige
      implementar (ou encontrar forma segura de embutir) geração real de
      QR com correção de erro.
- [ ] Lista de "amigos" é só histórico local, sem presença online — se
      isso virar requisito real no futuro, vai exigir reabrir a decisão
      de usar algum servidor leve de presença.

### Prioridade baixa / validado como não-bug
- Itens de uma lista de "42 bugs" trazida pelo usuário numa rodada
  anterior foram verificados individualmente contra o código real; vários
  eram falsos ou já estavam corrigidos antes da lista chegar (TNT
  explode normalmente, geometria já dá dispose corretamente, fog já é
  dinâmico, animais já não nascem na água). Não reabrir esses itens sem
  nova evidência concreta.

### Fases de conteúdo planejadas, não iniciadas
- [ ] Menu com sub-tela de configurações de servidor/skin (estrutura
      inspirada em Minecraft, não implementada ainda).
- [ ] CDN de texturas com sistema de qualidade (baixa/média/alta/ultra)
      documentado em mensagem do usuário, ainda não integrado ao motor
      atual (hoje as texturas são só o gerador procedural).
- [ ] Mecânicas na ordem histórica confirmada via pesquisa (Alpha →
      Beta 1.8 → 1.0 → 1.6 → 1.9 → 1.12): já existe fome/sprint/
      criativo-voo; faltam armadura como proteção real, encantamento,
      poções, o End, cavalos, sistema de combate com escudo.
  - Sistema de vida/fome já existe; **sede e temperatura, mencionados
    pelo usuário, ainda não foram implementados.**
- [ ] Hotbar de armadura (slots existem na hotbar de itens genérica, mas
      não há slots dedicados de equipamento nem sistema de defesa).

---

## 6. Perguntas já respondidas nesta conversa (para não repetir pesquisa)

- **Servidores oficiais do Minecraft**: não é crime conectar (protocolo é
  documentado publicamente e reimplementado por incontáveis projetos
  historicamente tolerados), mas o jogo não fala esse protocolo — exigiria
  reimplementá-lo do zero. Decisão: não vale o esforço, o multiplayer P2P
  já resolve a necessidade real sem entrar nessa zona cinzenta de "parecer
  Minecraft oficial".
- **Rust/Cargo**: `rustc`/`cargo` reais foram instalados e testados com
  sucesso (compilaram e rodaram um binário real). O bloqueio é só de
  rede (`crates.io`, `index.crates.io` bloqueados pela allowlist do
  ambiente) e falta da stdlib Android.
- **QR code**: pesquisado, decisão consciente de não implementar do zero
  sem poder testar em navegador real (algoritmo de correção de erro
  Reed-Solomon é não-trivial).
- **`sensorLandscape`**: confirmado como a mesma técnica usada por
  Unity/Unreal para travar em paisagem sem diálogo ao usuário.

---

## 7. Como retomar isso numa conversa nova

1. Suba o `voxelcraft.html` atual (v6.5.0) e este manual.
2. Peça para o Claude ler o manual inteiro antes de qualquer código.
3. Peça para ele **revalidar** (extrair JS, `node --check`, checar
   pareamento de blocos) antes de assumir que o arquivo enviado está no
   estado descrito aqui — arquivos podem ter sido editados manualmente
   entre uma conversa e outra.
4. Ataque a checklist da seção 5 por prioridade, um item por vez,
   testando cada correção isoladamente antes de integrar — é o método
   que sustentou a qualidade do projeto até aqui.
