# Bot "Só Mídia" — Power Xinin

## 1. Criar o bot (5 min)
1. Acesse https://discord.com/developers/applications → **New Application** → dê um nome.
2. Aba **Bot** → **Reset Token** → copie o token (não compartilhe com ninguém).
3. Ainda em **Bot**, ligue **MESSAGE CONTENT INTENT** (sem isso o bot não enxerga os anexos).
4. Aba **OAuth2 → URL Generator**: marque `bot` e `applications.commands`.
   Permissões: **Ver canais, Enviar mensagens, Gerenciar mensagens, Ler histórico de mensagens**.
5. Abra o link gerado e adicione o bot ao Power Xinin.

## 2. Configurar
- No Discord: Configurações → Avançado → ligue **Modo Desenvolvedor**.
- Clique com o botão direito no canal de mídias → **Copiar ID do canal**.
- Na hospedagem, crie as variáveis:
  - `DISCORD_TOKEN` = token do bot
  - `CANAIS_MIDIA` = ID do canal (vários? separe por vírgula)

## 3. Hospedar (24h, fora do seu computador)
- **Railway**: New Project → Deploy from GitHub repo → `bot-so-midia` → Variables.
  O `railway.json` já define o comando de início e reinício automático.
- **Discloud**: o `discloud.config` já está pronto.

## 4. Apagar as mensagens de texto que já existem
No canal de mídias, digite **/limpar-midias**. Só quem tem "Gerenciar mensagens" vê o comando.
⚠️ Não tem como desfazer. Mensagens fixadas e de bots são preservadas.
Mensagens com mais de 14 dias são apagadas uma por uma (limite do Discord), então canais grandes podem levar um tempo.

## Como funciona depois
- Foto/vídeo/arquivo (com ou sem legenda) → ✅ fica
- Resposta (reply) a uma foto/arquivo, mesmo só texto → ✅ fica
  (desligue em `RESPOSTAS_A_MIDIA_PODEM_TEXTO`)
- Só texto → 🗑️ apagado + aviso que some em 6 s
- Mandou foto e editou removendo o anexo → 🗑️ apagado
- Moderadores podem mandar texto (desligue em `MODS_PODEM_TEXTO`)

## Alternativa sem bot
Se o server for **Comunidade**, dá para criar um **Canal de Mídia** nativo do Discord
(Criar canal → "Mídia"): cada postagem exige uma imagem/vídeo. Porém, as respostas
dentro das postagens podem ser texto, e as mensagens antigas do canal atual não migram.
