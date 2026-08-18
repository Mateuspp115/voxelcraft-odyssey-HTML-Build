# Auditoria de cobertura e versionamento do VoxelCraft

## Resultado

A árvore de trabalho contém **14 snapshots HTML** e todos foram preservados em `versions/html/`. A versão `v14` é a mais recente, aparece no primeiro lugar dos índices e possui release e ZIP source-only próprios. A ausência de uma v10 foi mantida porque não existe snapshot correspondente no material organizado.

| Categoria | Conteúdo verificado |
|---|---:|
| Builds HTML | 14 |
| Manifests individuais | 14 |
| ZIPs source-only publicados | 14 |
| Casca mobile inicial | 1 |
| Variantes mobile v2 | 2 |
| Casca mobile v5 | 1 |
| Arquivos de documentação de referência | 9 |
| Diretório de screenshots | Preservado com README, pronto para capturas |
| APK/AAB gerado nesta revisão | 0 |

## Downloads

O índice [`../../versions/downloads/README.md`](../../versions/downloads/README.md) lista cada versão com commit, SHA-256, release e URL direto para o ZIP. As releases são source-only: cada archive contém apenas o HTML do snapshot correspondente.

## Cascas mobile

Os arquivos de WebView ficam em [`../../mobile-shells/`](../../mobile-shells/), fora da lista HTML. Seus commits históricos são `a7ab095`, `0f61c6a`, `ba63026` e `64ac380`, mantendo a evolução do empacotamento móvel separada do jogo HTML.

## Limite da comparação de origem

A pasta local `/home/ubuntu/voxelcreft-repo` é a extração organizada usada para publicar o repositório. O arquivo ZIP bruto original do VoxelCraft não está disponível no diretório de uploads desta sessão; portanto, esta auditoria confirma integralmente a cobertura da árvore extraída e do histórico Git local, mas não inventa uma comparação byte a byte com um ZIP que não está presente. Se o ZIP original for reenviado, o manifesto pode ser comparado diretamente contra ele.

Nenhum APK foi gerado. O repositório preserva código HTML, documentação, resources, screenshots e shells mobile, sem apresentar builds Android não verificadas como se fossem releases.
