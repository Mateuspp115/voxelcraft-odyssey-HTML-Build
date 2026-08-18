# Voxelcraft Odyssey — Arquivo de Builds HTML

> Coleção versionada do **Voxelcraft Odyssey**, um jogo em HTML inspirado em experiências de blocos, acompanhada dos materiais de build Android/WebView, documentação técnica e histórico de evolução fornecidos.

Este repositório foi organizado para preservar as builds como artefatos independentes: cada versão HTML mantém seu próprio `index.html`, cada casca mobile é rastreada separadamente e os documentos de manutenção continuam acessíveis sem misturar arquivos de leitura com o código do jogo.

## Estrutura

| Caminho | Conteúdo |
|---|---|
| [`versions/html/`](versions/README.md) | Quatorze builds HTML preservadas, da v1 à v14, incluindo variantes v6. |
| [`versions/downloads/`](versions/downloads/README.md) | ZIP source-only e release individual para cada build; v14 aparece primeiro. |
| [`versions/manifests/`](versions/README.md) | Manifesto arquivo por arquivo de cada snapshot. |
| [`mobile-shells/`](mobile-shells/README.md) | Cascas Android/WebView históricas para empacotamento mobile. |
| [`docs/`](docs/README.md) | Changelogs, checkpoints, manuais, auditorias e documentação do motor de texturas. |
| [`resources/`](resources/README.md) | Arquivos de referência mantidos como recebidos. |
| [`screenshots/`](screenshots/README.md) | Local reservado para capturas revisadas por versão e plataforma. |

## Downloads por versão

A build **v14** é a referência mais recente e aparece primeiro no [índice de downloads](versions/downloads/README.md). Cada versão possui um ZIP source-only independente, seu commit histórico e uma release GitHub. As cascas mobile são mantidas separadamente e não são confundidas com as builds HTML.

## Início rápido

1. Escolha uma versão em [`versions/html/`](versions/html/).
2. Abra o respectivo `index.html` em um navegador moderno.
3. Para uma referência técnica da build v14, consulte o [guia do motor de texturas](docs/reference/README_TEXTURE_ENGINE.md).

As versões foram preservadas como snapshots históricos. Antes de modificar uma delas, crie uma nova versão ou branch, registre as mudanças e valide em desktop e mobile.

## Histórico preservado

O conjunto recebido contém v1, v2, v3, v4, v5, v6 Lite, v6 Offline CDN Embutido, v7, v8, v9, v11, v12, v13 Beta e v14. A ausência de v10 no arquivo de origem foi mantida de forma intencional, sem inventar um snapshot inexistente.

## Auditoria e cobertura

O arquivo [`versions/manifest.json`](versions/manifest.json) registra hashes, tamanhos e origem de cada arquivo das 14 builds HTML. O [`versions/file-history.csv`](versions/file-history.csv) fornece a mesma informação em formato tabular. O diretório `docs/reference/` reúne a documentação de leitura, enquanto `screenshots/` permanece reservado para capturas futuras. Nenhuma versão v10 foi inventada, porque ela não estava presente no material recebido.

## Contribuição e manutenção

Cada contribuição deve indicar a build-base, descrever a mudança, informar como foi testada e anexar capturas revisadas quando houver alteração visual. Pacotes compactados são mantidos como referência e não devem ser executados sem inspeção.
