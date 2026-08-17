# Changelog — v6 (aplicado nesta conversa)

> Ainda não recebi o arquivo de patch que você mencionou que ia mandar — isso aqui é tudo que já estava combinado nas mensagens anteriores (bug do wifi, correções da casca, joystick). Quando o patch chegar, aplico em cima desta versão.

## 1. Bug do wifi — resolvido (jogo + casca)

Causa confirmada: 3 `<script src="https://...">` (Tailwind, Three.js r128, JSZip) + 3 tags de Google Fonts (`Press Start 2P`, `VT323`) no `<head>` — 6 pontos de rede no total, não 3 como eu tinha achado antes (as fontes eu só percebi ao reabrir o arquivo agora).

- **Three.js r128** e **JSZip 3.10.1**: peguei o código-fonte exato (mesma versão, via npm) e colei inteiro dentro de `<script>` no HTML.
- **Tailwind**: em vez de embutir o compilador JIT inteiro (~300KB+), gerei um CSS estático contendo só as classes que o jogo realmente usa (23,8KB) — mais rápido de carregar também, não só menor.
- **Google Fonts**: baixei os arquivos `.woff2` das duas fontes (subconjuntos latin + latin-ext, pra cobrir acento do português) e embuti em base64 via `@font-face`.
- Resultado: **0 requisições de rede** para o jogo abrir e rodar. `voxelcraft-odyssey_v6.html`: 224KB → 1,03MB. O único ponto de rede que sobrou é intencional — os servidores STUN do multiplayer (`stun.l.google.com`), que só são usados se você abrir uma sessão multiplayer, não pra jogar sozinho.
- Validado: extraí todo o JS do arquivo final e rodei `node --check` (sintaxe OK), e confirmei que os 27 blocos `@block:` continuam com 1 `:start` e 1 `:end` cada.

## 2. Controle / joystick — adicionado

Novo bloco `GamepadInput` (Gamepad API padrão do navegador), sem nenhuma lib nova. Soma-se ao teclado/mouse/touch, não substitui:

| Controle | Ação |
|---|---|
| Analógico esquerdo | mover |
| Analógico direito | olhar (câmera) |
| A | pular / subir voando |
| B | alternar voo (modo criativo) |
| Gatilho direito (RT) | minerar (segurar) |
| Gatilho esquerdo (LT) | colocar bloco |
| Bumpers (LB/RB) | trocar item da hotbar |
| Start | abrir/fechar inventário |

Detecta o controle automaticamente (sem precisa configurar nada), e some sozinho se for desconectado.

## 3. Casca Android — os 4 problemas encontrados na revisão anterior, corrigidos

- **`restartApp()`** agora relança o app de verdade (Intent com `FLAG_ACTIVITY_CLEAR_TOP`) em vez de só fechar o processo.
- **`onPermissionRequest`** não concede mais tudo automaticamente — só libera câmera, e só se a permissão Android já foi concedida de verdade. Microfone fica sempre negado (o jogo não usa). Isso fecha a brecha que o sistema de Mods abriria.
- **Trocado `file://` por origem `https://appassets.androidplatform.net/`** — escrevi um `shouldInterceptRequest` que serve o HTML local através dessa origem virtual, no mesmo espírito do `WebViewAssetLoader` do Google, mas sem adicionar essa biblioteca (o projeto não usa Gradle, e uma dependência nova que eu não consigo compilar aqui seria arriscado). Resolve o problema de `file://` não ser tratado como origem seguro (bloqueava Service Worker e é um padrão já documentado de causar bug perto de WebRTC).
- **`minSdkVersion` declarada** (23) — as correções acima usam APIs da 21/23; sem isso no manifest o padrão seria API 1.
- Linha redundante de `setMixedContentMode` removida.
- `assets/index.html` da casca atualizado para a versão nova (offline + joystick).

**O que eu não consegui validar 100%** (sem SDK Android real neste ambiente, igual a limitação que já existia): instalei um JDK aqui e rodei `javac` no arquivo — todos os erros retornados são de "pacote android.* não existe" (esperado, sem o `android.jar`), nenhum erro de sintaxe real. Chaves/parênteses conferem balanceados. Mas a primeira compilação de verdade com o SDK completo ainda precisa acontecer do seu lado — trate como primeiro teste de integração, é normal aparecer algum atrito pontual.

## Arquivos desta entrega
- `voxelcraft-odyssey_v6.html` — jogo atualizado (standalone, funciona em qualquer navegador).
- `android_webview_shell_v2.tar.xz` — casca Android corrigida, já com o `index.html` novo dentro.
