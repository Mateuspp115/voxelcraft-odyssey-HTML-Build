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

## 4. Geração de mundo — reescrita

**Diagnóstico dos 3 problemas relatados:**
- **Árvores incompletas**: confirmado — o desenho da copa (`spawnTree`) descartava qualquer folha que caísse fora dos limites locais do chunk (`px<0||px>=16...`). Árvore nascendo perto da borda perdia metade da copa, sempre. Corrigido: árvores agora são decididas e desenhadas numa passada que varre um pouco além da borda de cada chunk (margem de 2 blocos), e cada chunk desenha só a fatia da copa que cai dentro dele — testei isso especificamente (árvore na borda gx=-49: 15 blocos de folha no chunk de origem + 9 blocos completando no chunk vizinho, que antes eram perdidos).
- **Mar sem água**: a altura do terreno não tinha um ruído de "continentalidade" — só colina normal, então raramente descia o suficiente pra formar mar de verdade (só poças). Adicionei um ruído de frequência bem mais baixa que separa continente de oceano em regiões grandes e contíguas, com bacia oceânica de verdade (bem abaixo do nível do mar), calibrado pra ~20-30% de água no mundo.
- **Montanhas baixas sem neve**: neve dependia só do bioma horizontal (temperatura), nunca da altitude — um pico alto em bioma de floresta nunca nevava. Adicionei neve por elevação (independente do bioma) acima de uma altura fixa, e troquei o ruído de montanha por um "ridged noise" (cristas conectadas, picos afiados) em vez do morro arredondado de antes — montanhas ficaram bem mais altas e dramáticas dentro do limite de altura do mundo (`CHUNK_HEIGHT=64`, que mantive — mudar isso afetaria física/render/LOD em vários lugares, risco alto pra esta rodada).

**Novidades:**
- **Córregos**: canal estreito e sinuoso (com distorção de coordenada pra não ficar reto) que corta o terreno até quase o nível do mar e enche de água sozinho, usando a mesma regra de água que já existia.
- **Cavernas gigantes**: além dos túneis de antes, uma segunda camada de ruído bem mais grosso cria salas grandes e raras.
- **Ruínas abandonadas**: estruturas retangulares (5×5 a 9×9) com paredes de altura irregular (parecendo desmoronadas), buracos aleatórios na parede, entulho ocasional (cascalho/pedregulho) e tocha rara em trecho de parede que sobrou alto. São prédios individuais espalhados — não uma cidade planejada com ruas (isso seria um sistema de planejamento urbano à parte, bem maior); às vezes calham perto um do outro por acaso e formam um agrupamento.

**Eficiência (testei antes/depois em 961 chunks, mesma seed):** gerador antigo ≈1,1ms/chunk, novo ≈1,7ms/chunk — mais pesado por ter bem mais camadas de ruído (continente+cume+rio), o que é esperado dado o tanto de recurso novo. Otimizei o que dava (a checagem de árvore agora descarta ~95% das colunas antes de calcular ruído caro), e o sistema de carregamento de chunk já usa orçamento de TEMPO por frame (não quantidade fixa), então não deve causar engasgo — só um pop-in um pouco mais lento em deslocamento muito rápido.

**Validado**: rodei o gerador de verdade (com o `NoiseSystem`/`BlockDefs` reais extraídos do arquivo) numa área de 31×31 chunks, conferindo estatísticas (água, neve, ruína) e o caso específico da árvore na borda, além do `node --check` e pareamento de `@block:` no arquivo final. Não joguei no navegador — vale um teste visual seu antes de considerar fechado.

## 5. Reestruturação do CDN (a pedido) — arquivo leve de novo

Revertido: Three.js, JSZip, Tailwind e as fontes voltaram a ser carregados via link externo (`<script src=`/`<link href=`), em vez de embutidos. Arquivo caiu de 1,03MB para 244KB — mais rápido de abrir, editar e eu localizar coisas sem risco de um grep esbarrar dentro de uma biblioteca minificada gigante (isso realmente me atrapalhou numa rodada anterior).

O conteúdo já baixado e testado das 4 dependências foi salvo à parte, pronto pra quando for a hora de gerar a build offline:
- `cdn_modulo.zip` → `tailwind.offline.css`, `three.r128.min.js`, `jszip.3.10.1.min.js`, `fonts.offline.css`

O HTML agora tem um comentário no lugar exato de cada CDN explicando o que colar de qual arquivo quando for a hora. **Importante**: como a casca (`android_webview_shell_v2.tar.xz`) também foi atualizada com essa versão leve, ela **volta a precisar de internet** pra rodar — isso é temporário e esperado, o pacote fica pronto pra virar offline de novo com um pedido seu quando o jogo estiver mais fechado.

## 6. Correções desta rodada (interface + multiplayer + geração de mundo)

- **Engrenagem por mundo**: cada mundo na lista agora tem um botão ⚙ que abre um mini-formulário inline (nome + modo de jogo) sem precisar entrar no mundo.
- **Botão renomeado de verdade**: além do texto, ele agora *realmente* salva as configurações gráficas (antes elas não eram persistidas em lugar nenhum — fechar o jogo sempre resetava pra padrão, independente do botão).
- **"Modo de jogo" só aparece dentro do jogo**: escondido quando as configurações são abertas do menu principal, visível quando abertas da pausa.
- **Código de compartilhamento do multiplayer — bug real encontrado e corrigido**: tanto o lado anfitrião quanto o lado que entra esperavam o ICE gathering do WebRTC terminar sozinho antes de gerar o código; em rede restrita/móvel isso pode nunca disparar, travando a função pra sempre (parecia "não funcionar"). Adicionei um limite de 4s: se não terminar sozinho até lá, gera o código com o que já foi encontrado.
- **Montanhas com variedade de verdade**: agora ~60% viram planalto (topo achatado, dá pra caminhar em cima) e ~40% mantêm o pico afiado de antes — não é mais todo mundo do mesmo jeito.
- **Neve mais rara**: agora depende de altitude **e** de estar numa região fria (ruído separado, de baixa frequência) — pico alto fora dessa região vira rocha nua, não neve. Testei: ~66% dos picos altos nevam, resto fica rochoso.
- **Uma camada extra de ruído fino** pra quebrar regularidade visual notada no terreno.

## Itens que eu não consegui fechar sozinho (preciso de mais detalhe seu)

- **Botão JOGAR**: rastreei toda a cadeia (lista → `continueWorld` → `SaveSystem.load` → `enterGameUI` → loop principal) e está internamente consistente — não achei o bug parado no código. Me conta o que acontece exatamente ao clicar (nada visível? trava numa tela de carregando? erro no console do navegador?) que eu miro certo.
- **QR code**: confirmado que ainda não existe (o handoff anterior já registrava isso como decisão consciente de adiar). Se quiser que eu implemente agora, me avisa que entro nisso.
- **"Água ainda buga"**: revisei a lógica de preenchimento (tecnicamente parece correta) mas sem ver o jogo rodando não consigo apontar a causa exata — me descreve o que acontece (água falta em algum lugar? aparece flutuando? pisca?) ou manda print/vídeo se puder.

## Arquivos desta entrega
- `voxelcraft-odyssey_v6.html` — leve de novo (244KB), CDN referenciado.
- `cdn_modulo.zip` — as 4 dependências já prontas, guardadas pra quando for a hora de embutir.
- `android_webview_shell_v2.tar.xz` — `index.html` interno também voltou a ser a versão leve (temporariamente precisa de internet, ver seção 5).
