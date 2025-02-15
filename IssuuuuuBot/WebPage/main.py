from flask import Flask, request, render_template, redirect, url_for, flash, session
import os
import nextcord
from nextcord.ext import commands
import threading
import time
import secrets

# Configurações do Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
UPLOAD_FOLDER = 'WebPage/static/audios'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configurações do Bot do Discord
TOKEN = 'DIGITE_AQUI_O_TOKEN_DO_SEU_BOT'# Substitua pelo token do seu bot
intents = nextcord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Variável global para armazenar o cliente de voz
voice_client = None

# Senha de acesso
SENHA = "ESCOLHA_SUA_SENHA_PARA_O_PAINEL_WEB" # Altere para a senha que você desejar

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        senha = request.form['senha']
        if senha == SENHA:
            # Se a senha estiver correta, define uma sessão
            session['autenticado'] = True
            flash('Login bem-sucedido!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Senha incorreta!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('autenticado', None)  # Remove a sessão de autenticação
    flash('Você foi desconectado!', 'error')
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if not session.get('autenticado'):  # Verifica se o usuário está autenticado
        return redirect(url_for('login'))  # Redireciona para a página de login
    if request.method == 'POST':
        if 'audio' not in request.files:
            return redirect(request.url)
        file = request.files['audio']
        if file.filename == '' or len(file.filename) > 44:
            flash('Erro ao enviar o audio, verifique a quantidade de caracteres!', 'error')
            return redirect(request.url)
        if file:
            # Verifica se o arquivo é MP3
            if not file.filename.endswith('.mp3'):
                flash('Arquivo não suportado!', 'error')
                return redirect(url_for('index'))
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)

            flash('Áudio enviado com sucesso!', 'success')
            return redirect(url_for('index'))

    # Lista apenas arquivos MP3 na pasta UPLOAD_FOLDER
    audio_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.mp3')]
    return render_template("index.html", audio_files=audio_files)

@bot.event
async def on_ready():
    print(f'Bot {bot.user.name} está online!')
    # Verifica se o bot está conectado a algum canal de voz
    for guild in bot.guilds:
        if guild.voice_client and guild.voice_client.is_connected():
            print(f'Conectado ao canal de voz: {guild.voice_client.channel}')

# Rota para reproduzir áudio no Discord
@app.route('/play', methods=['POST'])
def play_audio():
    try:
        global voice_client
        audio_file = request.form['audio']
        audio_path = os.path.join(UPLOAD_FOLDER, audio_file)
        
        if voice_client.is_playing():
            voice_client.stop()
        # Reproduz o novo áudio
        voice_client.play(nextcord.FFmpegPCMAudio(audio_path), after=lambda e: print('Áudio terminou de tocar!'))

        return redirect(url_for('index'))
    except:
        flash('Bot não está conectado a um canal de voz. Use !join no Discord primeiro.', 'error')
        return redirect(url_for('index'))

@app.route('/delete', methods=['POST'])
def delete():
    try:
        audio_name = request.form.get('audio')  # get evita erro se o campo não existir
        if not audio_name:
            print("Nenhum arquivo recebido.")
            return redirect(url_for('index'))

        audio_path = os.path.join(UPLOAD_FOLDER, audio_name)  # Usa a variável global

        if os.path.exists(audio_path):
            os.remove(audio_path)
            flash(f'Arquivo {audio_name} removido!', 'success')
        else:
            flash(f'Arquivo {audio_path} não encontrado!', 'error')
        return redirect(url_for('index'))

    except Exception as e:
        flash(f"Erro ao deletar o arquivo: {e}", 'error')
        return redirect(url_for('index'))

# Comando do Bot para entrar no canal de voz
@bot.command(name='join')
async def join(ctx):
    global voice_client
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        # Verifica se o bot já está conectado a um canal de voz
        if ctx.voice_client and ctx.voice_client.is_connected():
            await ctx.send(f'Já estou conectado ao canal de voz: {ctx.voice_client.channel}')
        else:
                # Tenta conectar ao canal de voz com um timeout de 30 segundos
                voice_client = await channel.connect(timeout=5.0)
                await ctx.send(f'Conectado ao canal de voz: {channel}')
    else:
        await ctx.send('Você precisa estar em um canal de voz para usar este comando!')

# Comando do Bot para sair do canal de voz
@bot.command(name='leave')
async def leave(ctx):
    global voice_client
    if ctx.voice_client and ctx.voice_client.is_connected():
        await ctx.voice_client.disconnect()
        await ctx.send('Saindo do canal de voz.')
        voice_client = None  # Reseta a variável voice_client
        time.sleep(1)
    else:
        await ctx.send('Eu não estou em um canal de voz.')

# Função para rodar o bot do Discord em uma thread separada
def run_bot():
    bot.run(TOKEN)

# Inicia o bot do Discord em uma thread separada
threading.Thread(target=run_bot).start()

# Inicia o Flask
if __name__ == '__main__':
    app.run(debug=False)