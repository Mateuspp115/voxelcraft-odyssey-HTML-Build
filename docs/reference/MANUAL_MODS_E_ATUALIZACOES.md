# Manual: Sistema de Mods e Atualizações — VoxelCraft: Odyssey

Versão do jogo coberta por este manual: **6.2.0**

---

## 1. Visão geral — duas ferramentas diferentes

| | Mods | Atualizações |
|---|---|---|
| Formato do arquivo | `.mcmod` (ZIP) | `.patch` (ZIP) |
| Onde fica guardado | IndexedDB do navegador | Dentro do próprio HTML |
| Quem usa | Qualquer jogador | Só você (desenvolvedor) |
| O que pode tocar | Só a API pública (`window.VoxelCraft`) | Qualquer parte do código-fonte |
| Pode trocar o motor? | Não | Sim, completamente |
| Precisa reiniciar? | Recarregar a página (ou usar o botão de aplicar) | Não — tem um botão "aplicar ao vivo" |
| Sobrevive a recarregar a página? | Sim (fica salvo) | Só se você gerar e distribuir o novo `.html` |

A regra mais importante: **Atualizações conseguem fazer tudo que Mods conseguem, e muito mais. Mods nunca conseguem fazer o que só Atualizações fazem.**

---

## 2. Como criar um Mod (`.mcmod`)

Um `.mcmod` é um arquivo ZIP com esta estrutura:

```
meu_mod.mcmod
├── mod.json              (obrigatório)
├── codigo/
│   ├── blocos.js          (ou .ts — é transpilado automaticamente)
│   └── comportamento.ts
├── texturas/
│   └── meu_bloco.png
├── sons/
│   └── efeito.wav
└── data/
    └── itens.json
```

### `mod.json`

```json
{
  "id": "meu_mod_unico",
  "name": "Meu Primeiro Mod",
  "version": "1.0",
  "author": "Seu Nome",
  "description": "O que o mod faz"
}
```

`id` e `name` são obrigatórios. O `id` precisa ser único — se você reinstalar um mod com o mesmo `id`, ele substitui a versão anterior.

### Um script de mod básico (`codigo/exemplo.js`)

```javascript
VoxelCraftMod.register({
  id: "meu_mod_unico",
  name: "Meu Primeiro Mod",
  onInstall: function(api) {
    api.registerBlock("rubi", {
      name: "Bloco de Rubi",
      hardness: 900,
      drop: "self",
      renderType: "cube",
      solid: true,
      transparent: false,
      pattern: { top: "plain", side: "plain", bottom: "plain" },
      colorTop: "#c41e3a",
      colorSide: "#c41e3a",
      colorBottom: "#c41e3a"
    });
  }
});
```

Você também pode escrever em TypeScript (`codigo/exemplo.ts`) — o jogo transpila para JavaScript automaticamente ao instalar. Se houver erro de tipo grave, a instalação é recusada com a mensagem do erro.

### O que um Mod NÃO pode fazer (por segurança)

O instalador recusa qualquer script que tente referenciar: `parsePatch`, `applyManifest`, `VoxelCraftUpdater`, `ModStorage`, `TSTranspiler`, `window.location`, `document.write`, `eval(`. Isso impede que um mod malicioso (ou com bug) acesse o sistema de Atualizações ou o próprio armazenamento de mods.

### Instalando

Dentro do jogo: menu principal → **MODS** → **Escolher .mcmod**. O mod aparece na lista, com botões para ativar/desativar, escolher escopo (todos os mundos, ou só mundos específicos), e remover. Se algo der erro, o log aparece embaixo do nome do mod.

---

## 3. Como criar uma Atualização (`.patch`)

Um `.patch` também é um ZIP:

```
minha_atualizacao.patch
├── manifest.patch         (obrigatório — é um JSON, apesar da extensão)
├── scripts/
│   └── algumacoisa.js
└── assets/
    ├── nova_textura.png
    ├── som_novo.wav
    ├── efeito.glsl
    └── fonte.ttf
```

### `manifest.patch`

```json
{
  "name": "Nome da atualização",
  "version": "6.3.0",
  "author": "Você",
  "description": "O que essa atualização muda",
  "commands": [
    { "op": "...", "...": "..." }
  ]
}
```

### Lista de comandos disponíveis

| Comando | Parâmetros | O que faz |
|---|---|---|
| `ADD` | `name`, `content` (ou `contentFrom`), e um de `after`/`before`/`atEnd` | Insere um bloco novo. Recusa automaticamente se o código declarar uma função/classe/const que já existe (a não ser que `allowNameConflict:true`). |
| `REPLACE` | `block`, `find`, `with`, `allowMultiple?` | Troca um texto exato dentro de um bloco. Se o texto não for encontrado, ou aparecer mais de uma vez sem `allowMultiple`, recusa sem alterar nada. |
| `REMOVE` | `block` | Apaga um bloco inteiro. |
| `MOVE` | `block`, e um de `before`/`after` | Reordena um bloco para outra posição. |
| `RENAME` | `block`, `to` | Renomeia um bloco. |
| `COPY` | `block`, `as` | Duplica um bloco com outro nome (o original continua existindo). |
| `MERGE` | `block`, `constName`, `data` | Adiciona chaves a um objeto `const NOME = {...}` existente. |
| `BACKUP` | `block` | Guarda uma cópia do bloco na memória desta aplicação de patch. |
| `RESTORE` | `block` | Devolve o bloco ao estado salvo pelo `BACKUP` mais recente. |
| `VERIFY` | — | Confere se todo o JavaScript do arquivo ainda é sintaticamente válido. Se não for, a atualização inteira é rejeitada. |
| `IF` / `ELSE` / `ENDIF` | `condition: "blockExists('Nome')"` ou `"not blockExists('Nome')"` | Aplica comandos condicionalmente. |
| `RUN` | `script` (nome de arquivo em `scripts/`) | Executa um script JS do pacote uma única vez, no momento da aplicação do patch. |
| `ENABLE` / `DISABLE` | `feature` | Marca uma feature (sem efeito automático — serve para scripts lerem essa marcação). |
| `IMPORT` / `EXPORT` | `package` / `data` | Registra intenção de importar/exportar (uso avançado). |

### Exemplo real: corrigir uma única linha com bug

```json
{
  "name": "Correção de bug",
  "version": "6.2.1",
  "commands": [
    { "op": "BACKUP", "block": "VoxelWorld" },
    { "op": "REPLACE", "block": "VoxelWorld", "find": "if (x) { y(); }}", "with": "if (x) { y(); }" },
    { "op": "VERIFY" }
  ]
}
```

O `BACKUP` antes garante que, se algo mais der errado depois, dá para usar `RESTORE` para voltar exatamente ao estado anterior daquele bloco.

### Conversão automática de assets

Qualquer arquivo dentro de `assets/` é convertido sozinho, sem você escrever código de conversão:

| Extensão | Vira... |
|---|---|
| `.png`, `.jpg`, `.gif`, `.webp` | Textura comprimida (RLE quando vantajoso) e registrada via `VoxelCraftAssets.registerTexture` |
| `.wav`, `.ogg`, `.mp3` | Som decodificado, convertido para PCM Int16 comprimido, via `VoxelCraftAssets.registerSound` |
| `.glsl`, `.vert`, `.frag` | Shader registrado via `VoxelCraftAssets.registerShader` |
| `.ttf`, `.otf` | Fonte registrada via `VoxelCraftAssets.registerFont` |

Cada arquivo vira automaticamente um comando `ADD` no final da aplicação do patch — você não precisa escrever nada no `manifest.patch` para isso acontecer.

### Aplicando uma Atualização

Dentro do jogo: menu principal → **ATUALIZAÇÕES (DESENVOLVEDOR)** → selecione o `.patch` → **VALIDAR**. O sistema:

1. Aplica os comandos numa cópia em memória (o jogo rodando não é afetado ainda).
2. Roda `VERIFY` de sintaxe.
3. Confere se a estrutura essencial (`window.VoxelCraft`, `<canvas id="game-canvas">`, etc.) continua presente.
4. Carrega o resultado num `<iframe>` escondido e isolado, para ver se ele inicializa sem erros de verdade.

Se tudo passar, dois botões aparecem:
- **APLICAR AGORA NESTA PÁGINA (AO VIVO)** — injeta o código novo na página que está rodando agora, sem recarregar.
- **BAIXAR HTML PARA DISTRIBUIR** (ou **INSTALAR ATUALIZAÇÃO**, dentro do app Tauri) — gera o arquivo `.html` completo e atualizado, para você distribuir para outras pessoas/máquinas.

### Detecção automática de conflitos (desde a v6.2)

Todo comando `ADD` agora verifica sozinho se o código que está sendo inserido declara uma `function`, `class`, `const` ou `let` no nível mais externo que **já existe** em outro lugar do arquivo. Se existir, o patch inteiro é recusado com uma mensagem dizendo exatamente qual nome colidiu — antes mesmo de tentar aplicar, evitando o tipo de bug onde duas atualizações sem querer redeclaram a mesma coisa e quebram o jogo silenciosamente. Se a sobreposição for proposital (por exemplo, você quer uma versão nova de uma classe e vai remover a antiga separadamente com `REMOVE`), use `"allowNameConflict": true` nesse comando `ADD`.

---

## 4. Edição manual vs. sistema de Atualizações — qual usar?

**Edição manual direta no HTML** (peça para o Claude reescrever um trecho inteiro): melhor para mudanças **grandes e estruturais** — redesenhar uma classe inteira do zero, trocar a abordagem de um sistema completo. Mais rápido quando a mudança é ampla demais para descrever como uma lista de comandos pequenos.

**Sistema de `.patch`**: melhor para mudanças **cirúrgicas, pequenas, e que você quer documentar**. Cada `.patch` vira um registro permanente do que mudou e por quê — como um commit do Git. Também é a única opção se você quer testar a mudança antes de aceitá-la (o pipeline de validação), ou se quer aplicar a mesma mudança em várias cópias diferentes do jogo de forma confiável.

Na prática, o ideal é misturar os dois: peça edição manual para reformas grandes, e gere `.patch` para correções e adições incrementais que valem a pena ficar registradas.

---

## 5. A ordem real dos 23 blocos modulares do jogo

Esta é a ordem exata em que os blocos aparecem hoje no arquivo (versão 6.2.0). Comandos `MOVE`/`before`/`after` se referem a estes nomes:

```
 1. BlockDefs           — definição de todos os 54 blocos/itens do jogo
 2. BlockRegistry        — calcula IDs, lookups de solidez/transparência
 3. TextureGenerator     — desenha cada padrão de textura num canvas 16x16
 4. TextureAtlas         — monta o atlas de texturas (todas as faces de todos os blocos)
 5. NoiseSystem          — ruído Perlin determinístico (seedado)
 6. WorldGenerator       — geração de terreno, biomas, cavernas, minérios, árvores
 7. SoundFX              — sons sintetizados via WebAudio
 8. RaycastEngine        — raycast voxel (DDA) para mirar/minerar/colocar blocos
 9. VoxelWorld           — chunks, malha, edições, luzes, persistência de seed+edits
10. SimpleAnimal         — mobs passivos (vaca, ovelha, galinha, porco)
11. LODManager           — horizonte distante (heightmap simplificado)
12. PlayerCharacter      — física do jogador, vida/fome/respiração, mineração
13. SkyCycle             — ciclo dia/noite, céu, estrelas
14. SaveSystem           — salvamento local (localStorage)
15. GameBootstrap        — inicialização do motor, loop principal, UI do HUD
16. HooksAndAPI          — pontos de extensão (Hooks) e a API pública window.VoxelCraft
17. ChangelogV61         — registro de mudanças (exemplo de bloco adicionado por patch)
18. ModSystem            — runtime de Mods (.mcmod): transpilador TS, IndexedDB, segurança
19. AssetRuntime         — registrador de texturas/sons convertidos
20. ConflictDetector     — detector de conflitos de nomes (adicionado na v6.2)
21. UpdateSystem         — sistema de Atualizações: interpretador de patch, conversores, plataforma
22. ModsUI               — interface da tela de Mods
23. UpdaterUI            — interface da tela de Atualizações
```

Use `blockExists('NomeDoBloco')` dentro de uma condição `IF` para checar se um bloco existe antes de mexer nele — útil quando uma atualização pode ser aplicada tanto em versões antigas quanto novas do jogo.

---

## 6. A API final (`window.VoxelCraft`)

No fim do arquivo, depois de todo o motor carregado, existe um único objeto global que serve como ponto de entrada documentado para qualquer coisa externa (mods, consoles do navegador, futuras ferramentas):

```javascript
window.VoxelCraft = {
  Hooks,                          // objeto com arrays de callbacks (veja abaixo)
  BlockDefs,                      // o dicionário completo de definições de blocos
  getBlockKeys: () => [...],      // nomes de todos os blocos registrados agora
  getBlockById: () => [...],      // array indexado por ID numérico
  getWorld: () => gameWorld,      // instância atual de VoxelWorld (ou null fora de jogo)
  getPlayer: () => gamePlayer,    // instância atual de PlayerCharacter (ou null)
  getScene: () => mainScene,      // a cena Three.js
  registerBlock: (key, def) => ...,  // atalho para adicionar um bloco novo em tempo real
  mods: {
    list: () => Promise<mods[]>,
    installMcmod: (zipBytes) => Promise<mod>,
    remove: (id) => Promise,
    setEnabled: (id, enabled) => Promise
  },
  updates: {
    process: (zipBytes, sourceHtml) => Promise<resultado>
  },
  version: '6.2.0'
};
```

### `Hooks` — pontos de extensão por evento

```javascript
const Hooks = {
  onSetBlock: [],       // fn(x, y, z, blockId) — toda vez que um bloco é colocado/removido
  onBreak: [],           // fn(raycastResult, blockDef) — bloco minerado com sucesso
  onChunkBuilt: [],      // fn(chunkX, chunkZ) — malha de um chunk (re)construída
  onPlayerDamaged: [],   // fn(amount, cause) — jogador tomou dano
  onPlayerDeath: [],     // fn() — jogador morreu
  onFrame: []            // fn(deltaMs) — uma vez por frame, enquanto em jogo
};
```

Para reagir a um evento, basta dar `push` numa função nesse array — por exemplo: `window.VoxelCraft.Hooks.onBreak.push((r, def) => console.log('quebrou', def.name))`.

---

## 7. O que é reutilizável fora deste jogo

Esta seção é para quando você (ou um motor de jogos futuro seu) quiser aproveitar peças deste sistema em outro projeto — incluindo jogos que não são de blocos, 2D ou 3D.

### Totalmente genérico, zero dependência de Minecraft/voxel

Estas peças não sabem nada sobre blocos, chunks ou voxels — dá para copiar e colar em **qualquer** projeto HTML/JS, jogo ou não:

- **`PatchInterpreter` + `PatchBlocks`** (sistema de blocos `@block:NOME:start/end` + comandos `ADD/REPLACE/REMOVE/MOVE/RENAME/COPY/MERGE/BACKUP/RESTORE/VERIFY/IF/ELSE/ENDIF`). Isso é, na prática, um **motor de patches de código-fonte genérico**. Funciona em qualquer arquivo de texto estruturado em blocos nomeados — não precisa ser um jogo. Dá para usar para atualizar qualquer aplicação HTML de página única.
- **`ConflictDetector`** (`extractTopLevelNames` + `checkNameConflicts`). Um analisador de JavaScript de propósito geral que detecta redeclarações de `function/class/const/let` no nível mais externo, ignorando strings/comentários/escopos internos corretamente. Útil em qualquer ferramenta que gere ou injete código JS dinamicamente.
- **`TSTranspiler`** (transpilador TypeScript→JavaScript simplificado, no navegador). Reutilizável em qualquer sistema de plugins/scripts que queira aceitar TypeScript sem depender de um build externo.
- **`AssetConverter`** (PNG→módulo JS comprimido, áudio→módulo JS comprimido, GLSL→string, fonte→FontFace). Esse pipeline de "asset vira código-fonte versionável" é útil para qualquer projeto que precise embutir mídia dentro de um único arquivo distribuível, jogo ou não (visualizadores de dados, apps offline, protótipos sem servidor).
- **`SoundFX`** (síntese de som via WebAudio sem arquivos externos). Os métodos auxiliares (`blip`, `thud`) são genéricos — dá para reaproveitar a técnica para qualquer jogo 2D/3D que queira efeitos sonoros sem baixar arquivos de áudio.
- **O esquema A/B da casca Tauri** (`install_update`/`revert_to_previous`/`cleanup_old_versions`/`restart_app` em `main.rs`). Esse padrão de "casca nativa que só carrega um arquivo de conteúdo versionado" é genérico para **qualquer** aplicação Tauri que precise se atualizar sem passar por uma loja de apps — não tem nada específico de jogo ali.
- **`VoxelCraftPlatform`** (detecção de ambiente + ponte com `invoke` do Tauri + fallback de download). Útil como padrão para qualquer app HTML que precise rodar tanto solto no navegador quanto dentro de uma casca nativa.

### Específico de jogos, mas não de jogos de blocos

Estas peças assumem "é um jogo" mas não assumem voxels/cubos — dá para reaproveitar em jogos 2D ou 3D de qualquer estilo:

- **A arquitetura de Mods inteira** (`ModSystem`, `ModStorage` via IndexedDB, formato `.mcmod`, lista de segurança de identificadores proibidos). O conceito — pacote ZIP com `mod.json` + código + assets, instalado no navegador do jogador, com escopo por "save"/mundo — serve para qualquer jogo que queira suportar mods de jogador final.
- **`Hooks`** (o padrão de arrays de callback por evento, e a própria ideia de manter uma API pública estável `window.SeuJogo` no fim do arquivo). É um padrão de design reutilizável, não uma implementação amarrada a blocos.
- **`raycastVoxel` (DDA)**: tecnicamente é especificamente voxel — mas o **padrão Amanatides & Woo** de raycast em grade é a base de qualquer jogo em grade 2D também (tile-based), só mudando de 3 para 2 dimensões.

### Específico deste jogo (não vale a pena extrair)

`BlockDefs`, `WorldGenerator`, `VoxelWorld`, `PlayerCharacter`, `SimpleAnimal`, `LODManager`, `SkyCycle` — esses sabem profundamente sobre blocos/chunks/voxels e física de personagem em primeira pessoa. Dá para usar como **referência de como estruturar** esses sistemas num jogo novo, mas não para copiar e colar.

### Para um motor de jogos seu, no futuro

Se a ideia é eventualmente ter um motor genérico seu, a base mais valiosa deste projeto não é o jogo em si — é a combinação de **(1)** blocos de código endereçáveis por nome, **(2)** um interpretador de comandos sobre esses blocos, **(3)** um pipeline de assets que vira código-fonte, e **(4)** dois sistemas de extensão com níveis de confiança diferentes (Mods restritos por API vs. Atualizações com acesso total, ambos com validação automática antes de aceitar). Essas quatro ideias juntas formam, na prática, um sistema de build e plugins independente de gênero de jogo — o resto (voxel, blocos, sobrevivência) é só o primeiro produto construído em cima dessa base.
