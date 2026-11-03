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
TOKEN = os.getenv("DISCORD_TOKEN", "")

# ID(s) do(s) canal(is) de mídia, separados por vírgula, na variável
# CANAIS_MIDIA da hospedagem. Ex.: CANAIS_MIDIA=123456789012345678
CANAIS_MIDIA = {
    int(x) for x in os.getenv("CANAIS_MIDIA", "").replace(" ", "").split(",") if x
}

# Moderadores (quem tem "Gerenciar mensagens") podem mandar texto normal?
MODS_PODEM_TEXTO = True

# Respostas (reply) a uma mensagem que tem foto/arquivo podem ser só texto?
RESPOSTAS_A_MIDIA_PODEM_TEXTO = True

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
    for cid in CANAIS_MIDIA:
        ch = client.get_channel(cid)
        if ch is None:
            print(f"AVISO: o ID {cid} não é um canal que o bot enxerga "
                  f"(pode ser ID do servidor, de mensagem ou de outro lugar).")
        else:
            print(f"Canal {cid}: #{ch.name} (tipo {ch.type}) no servidor {ch.guild.name}")


def eh_canal_midia(canal) -> bool:
    """Canal configurado, ou tópico/post dentro dele."""
    if canal is None:
        return False
    return canal.id in CANAIS_MIDIA or getattr(canal, "parent_id", None) in CANAIS_MIDIA


def responde_midia_conhecida(msg: discord.Message) -> bool:
    """True se a mensagem é resposta a uma mensagem que tem foto/arquivo
    (usa a mensagem original que o Discord já manda junto)."""
    ref = msg.reference
    if not ref or not isinstance(ref.resolved, discord.Message):
        return False
    return tem_midia(ref.resolved)


async def responde_midia(msg: discord.Message) -> bool:
    """Igual à de cima, mas busca a mensagem original se ela não veio junto."""
    ref = msg.reference
    if not ref or not ref.message_id:
        return False
    original = ref.resolved
    if not isinstance(original, discord.Message):
        try:
            original = await msg.channel.fetch_message(ref.message_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return False
    return tem_midia(original)


async def checar(msg: discord.Message):
    if not eh_canal_midia(msg.channel) or deve_ignorar(msg):
        return
    if tem_midia(msg):
        return
    if RESPOSTAS_A_MIDIA_PODEM_TEXTO and await responde_midia(msg):
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
    if not eh_canal_midia(canal):
        await interaction.response.send_message(
            "Use este comando dentro de um canal de mídia configurado.\n"
            f"ID deste canal: `{canal.id}` (tipo: {canal.type})\n"
            f"Canais configurados: {', '.join(f'`{c}`' for c in CANAIS_MIDIA)}",
            ephemeral=True)
        return

    await interaction.response.send_message(
        "🧹 Limpando mensagens só de texto... isso pode demorar em canais grandes.",
        ephemeral=True)

    def apagar(m: discord.Message) -> bool:
        # Na limpeza, apaga texto de todo mundo (menos fixadas e bots)
        if m.pinned or m.author.bot or tem_midia(m):
            return False
        if m.type not in (discord.MessageType.default, discord.MessageType.reply):
            return False
        if RESPOSTAS_A_MIDIA_PODEM_TEXTO and responde_midia_conhecida(m):
            return False  # resposta a uma foto/arquivo: mantém
        return True

    # purge apaga em lote as < 14 dias e uma a uma as mais antigas
    apagadas = await canal.purge(limit=None, check=apagar, bulk=True)
    await interaction.followup.send(
        f"✅ Pronto! {len(apagadas)} mensagens de texto removidas.", ephemeral=True)


if __name__ == "__main__":
    if not TOKEN or not CANAIS_MIDIA:
        raise SystemExit("Defina as variáveis DISCORD_TOKEN e CANAIS_MIDIA.")
    client.run(TOKEN)
