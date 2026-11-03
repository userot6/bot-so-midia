"""
Bot "Só Mídia" para o server Power Xinin.

O que ele faz:
  1. Apaga automaticamente qualquer mensagem SEM anexo (foto, vídeo, arquivo)
     enviada no(s) canal(is) de mídia configurado(s).
     -> Texto só é permitido junto com um anexo (como legenda).
  2. Comando /limpar-midias: varre o histórico do canal e apaga todas as
     mensagens antigas que são só texto.

Requisitos: Python 3.10+  e  pip install -U discord.py
"""

import asyncio
import os

import discord
from discord import app_commands

# ===================== CONFIGURAÇÃO =====================
TOKEN = os.getenv("DISCORD_TOKEN", "COLE_SEU_TOKEN_AQUI")

# ID(s) do(s) canal(is) de mídia. Clique com o botão direito no canal ->
# "Copiar ID do canal" (precisa do Modo Desenvolvedor ligado nas configurações).
CANAIS_MIDIA = {
    123456789012345678,
}

# Moderadores (quem tem "Gerenciar mensagens") podem mandar texto normal?
MODS_PODEM_TEXTO = True

# Links de imagem/vídeo (ex.: tenor, imgur, youtube) contam como mídia?
PERMITIR_LINKS_COM_PREVIA = True

# Aviso temporário para quem mandar só texto (some depois de X segundos)
MENSAGEM_AVISO = (
    "{user}, este canal é só para mídias! 📸 "
    "Envie uma foto ou arquivo — o texto pode ir junto como legenda."
)
SEGUNDOS_AVISO = 6
# ========================================================

intents = discord.Intents.default()
intents.message_content = True  # obrigatório para ler anexos/conteúdo

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)


def tem_midia(msg: discord.Message) -> bool:
    """True se a mensagem tem foto/arquivo (ou link com prévia, se permitido)."""
    if msg.attachments:
        return True
    if msg.stickers:
        return False  # figurinha não conta como mídia; mude para True se quiser
    if PERMITIR_LINKS_COM_PREVIA:
        if any(e.type in ("image", "video", "gifv") for e in msg.embeds):
            return True
        # A prévia do link às vezes chega um instante depois; checa o texto também
        texto = msg.content.lower()
        if any(s in texto for s in ("http://", "https://")) and any(
            x in texto for x in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp4",
                                 "tenor.com", "imgur.com", "youtu")
        ):
            return True
    return False


def deve_ignorar(msg: discord.Message) -> bool:
    if msg.author.bot or msg.pinned:
        return True
    if msg.type not in (discord.MessageType.default, discord.MessageType.reply):
        return True  # mensagens de sistema (boost, fixou mensagem etc.)
    if MODS_PODEM_TEXTO and isinstance(msg.author, discord.Member):
        if msg.channel.permissions_for(msg.author).manage_messages:
            return True
    return False


@client.event
async def on_ready():
    await tree.sync()
    print(f"Online como {client.user}. Vigiando canais: {CANAIS_MIDIA}")


async def checar(msg: discord.Message):
    if msg.channel.id not in CANAIS_MIDIA or deve_ignorar(msg):
        return
    if tem_midia(msg):
        return
    try:
        await msg.delete()
        await msg.channel.send(
            MENSAGEM_AVISO.format(user=msg.author.mention),
            delete_after=SEGUNDOS_AVISO,
        )
    except discord.Forbidden:
        print("Sem permissão para apagar mensagens nesse canal.")
    except discord.NotFound:
        pass


@client.event
async def on_message(msg: discord.Message):
    await checar(msg)


@client.event
async def on_message_edit(antes: discord.Message, depois: discord.Message):
    # Impede o truque de mandar foto e depois editar removendo o anexo
    await checar(depois)


@tree.command(name="limpar-midias",
              description="Apaga todas as mensagens só de texto deste canal de mídia")
@app_commands.default_permissions(manage_messages=True)
@app_commands.guild_only()
async def limpar_midias(interaction: discord.Interaction):
    canal = interaction.channel
    if canal.id not in CANAIS_MIDIA:
        await interaction.response.send_message(
            "Use este comando dentro de um canal de mídia configurado.", ephemeral=True)
        return

    await interaction.response.send_message(
        "🧹 Limpando mensagens só de texto... isso pode demorar em canais grandes.",
        ephemeral=True)

    def apagar(m: discord.Message) -> bool:
        # Na limpeza, apaga texto de todo mundo (menos fixadas e bots)
        return not m.pinned and not m.author.bot and not tem_midia(m) \
            and m.type in (discord.MessageType.default, discord.MessageType.reply)

    # purge apaga em lote as < 14 dias e uma a uma as mais antigas
    apagadas = await canal.purge(limit=None, check=apagar, bulk=True)
    await interaction.followup.send(
        f"✅ Pronto! {len(apagadas)} mensagens de texto removidas.", ephemeral=True)


if __name__ == "__main__":
    client.run(TOKEN)
