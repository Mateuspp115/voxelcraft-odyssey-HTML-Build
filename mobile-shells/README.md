# Cascas para build mobile

Esta pasta preserva os pacotes de casca Android/WebView recebidos junto às versões HTML. Eles são artefatos históricos de empacotamento, não uma garantia de build atual.

| Arquivo | Papel histórico |
|---|---|
| `android_webview_shell.tar.xz` | Casca Android/WebView inicial. |
| `android_webview_shell_v2.tar lite.xz` | Variante leve da casca v2. |
| `android_webview_shell_v2.tar.xz` | Casca Android/WebView v2. |
| `android_webview_shell_v5.tar.xz` | Casca Android/WebView v5. |

Cada pacote recebe um commit próprio para que seu histórico fique separado do histórico das builds HTML. Os commits históricos registrados são `a7ab095` (casca inicial), `0f61c6a` (variante v2 lite), `ba63026` (v2) e `64ac380` (v5). O arquivo `android_webview_shell_v5.sha256` preserva a verificação da casca v5.

As cascas não são contadas como versões HTML e ficam fora do índice `versions/downloads/`. Elas permanecem acessíveis pela árvore do repositório e por seus commits próprios.
