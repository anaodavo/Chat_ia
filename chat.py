import uuid
from flask import Flask, render_template_string, request, redirect, url_for
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'chave_secreta_segura'
socketio = SocketIO(app, async_mode='threading')

# Banco de dados na memória com as flags 'suspenso' e 'banido'
contas = [
    {"login": "admin", "senha": "adminpassword", "is_admin": True, "suspenso": False, "banido": False},
    {"login": "ola", "senha": "211", "is_admin": False, "suspenso": False, "banido": False},
    {"login": "jose", "senha": "hacker", "is_admin": False, "suspenso": False, "banido": False},
    {"login": "jose2", "senha": "hacker", "is_admin": False, "suspenso": False, "banido": False},
    {"login": "king", "senha": "hn", "is_admin": False, "suspenso": False, "banido": False},
    {"login": "gg", "senha": "1234", "is_admin": True, "suspenso": False, "banido": False}
]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Sistema de Gestão e Chat</title>
    <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 30px; background-color: #f4f4f9; color: #333; }
        .box { background: white; padding: 25px; border-radius: 8px; box-shadow: 0 0 12px rgba(0,0,0,0.1); max-width: 500px; margin: auto; }
        .box-large { max-width: 900px; }
        input, select { width: 90%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 4px; }
        button { width: 95%; padding: 10px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; margin-top: 5px; font-weight: bold; }
        .btn-blue { background: #007bff; }
        .btn-orange { background: #fd7e14; }
        .btn-danger { background: #dc3545; }
        .btn-success { background: #28a745; }
        .error { color: red; font-weight: bold; } .success { color: green; font-weight: bold; }
        a { display: block; margin-top: 15px; text-align: center; color: #007bff; text-decoration: none; }
        
        /* Chat e ID */
        #chat-container { border: 1px solid #ccc; border-radius: 4px; height: 220px; overflow-y: auto; padding: 10px; margin-bottom: 10px; background: #fafafa; }
        .msg-item { margin-bottom: 8px; font-size: 14px; border-bottom: 1px solid #f0f0f0; padding-bottom: 4px; }
        .msg-id { font-size: 10px; color: #999; display: block; }
        .msg-user { font-weight: bold; color: #007bff; }
        .msg-admin { font-weight: bold; color: #dc3545; }
        
        /* Seção de Figurinhas */
        .sticker-container { margin: 5px 0 12px 0; display: flex; gap: 8px; flex-wrap: wrap; }
        .sticker-btn { background: #e9ecef; border: 1px solid #ced4da; font-size: 20px; padding: 5px 10px; border-radius: 4px; cursor: pointer; transition: 0.2s; }
        .sticker-btn:hover { background: #dee2e6; transform: scale(1.1); }

        .grid-admin { display: grid; grid-template-columns: 1.2fr 1fr; gap: 20px; }
        .tabela-usuarios { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }
        .tabela-usuarios th, .tabela-usuarios td { border: 1px solid #ddd; padding: 6px; text-align: left; }
        .tabela-usuarios th { background-color: #f2f2f2; }
        #alerta-denuncia { display: none; background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; padding: 10px; border-radius: 4px; margin-bottom: 15px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="box {% if passo == 'admin_painel' %}box-large{% endif %}">
        
        {% if passo == 'login' %}
            <h2>Login</h2>
            {% if erro %} <p class="error">{{ erro }}</p> {% endif %}
            {% if msg %} <p class="success">{{ msg }}</p> {% endif %}
            <form method="POST" action="/login">
                <input type="text" name="login" placeholder="Usuário" required><br>
                <input type="password" name="senha" placeholder="Senha" required><br>
                <button type="submit">Entrar</button>
            </form>

        {% elif passo == 'admin_painel' %}
            <h2>Painel do Administrador</h2>
            <div id="alerta-denuncia"></div>
            
            {% if msg %} <p class="success">{{ msg }}</p> {% endif %}
            {% if erro %} <p class="error">{{ erro }}</p> {% endif %}
            
            <div class="grid-admin">
                <div>
                    <h3>Cadastrar Novo Usuário</h3>
                    <form method="POST" action="/criar_conta">
                        <input type="text" name="novo_usuario" placeholder="Novo Usuário" required><br>
                        <input type="password" name="nova_senha" placeholder="Senha" required><br>
                        <button type="submit" class="btn-blue">Criar Conta</button>
                    </form>
                    
                    <h3>Gerenciar Contas Ativas</h3>
                    <table class="tabela-usuarios">
                        <tr>
                            <th>Usuário</th>
                            <th>Status</th>
                            <th>Ações</th>
                        </tr>
                        {% for conta in todas_contas %}
                            {% if not conta.is_admin and not conta.banido %}
                            <tr>
                                <td>{{ conta.login }}</td>
                                <td>
                                    {% if conta.suspenso %}
                                        <span style="color: orange; font-weight: bold;">Suspenso</span>
                                    {% else %}
                                        <span style="color: green;">Ativo</span>
                                    {% endif %}
                                </td>
                                <td>
                                    <form method="POST" action="/modificar_conta" style="display:inline;">
                                        <input type="hidden" name="usuario_alvo" value="{{ conta.login }}">
                                        {% if conta.suspenso %}
                                            <button type="submit" name="acao" value="reativar" class="btn-orange" style="width:auto; padding:3px 6px; font-size:11px;">Reativar</button>
                                        {% else %}
                                            <button type="submit" name="acao" value="suspender" class="btn-orange" style="width:auto; padding:3px 6px; font-size:11px;">Suspender</button>
                                        {% endif %}
                                        <button type="submit" name="acao" value="banir" class="btn-danger" style="width:auto; padding:3px 6px; font-size:11px;">Banir</button>
                                    </form>
                                </td>
                            </tr>
                            {% endif %}
                        {% endfor %}
                    </table>

                    <h3>Usuários Banidos</h3>
                    <table class="tabela-usuarios">
                        <tr>
                            <th>Usuário</th>
                            <th>Ações</th>
                        </tr>
                        {% set tem_banidos = false %}
                        {% for conta in todas_contas %}
                            {% if conta.banido %}
                            <tr>
                                <td>{{ conta.login }}</td>
                                <td>
                                    <form method="POST" action="/modificar_conta" style="display:inline;">
                                        <input type="hidden" name="usuario_alvo" value="{{ conta.login }}">
                                        <button type="submit" name="acao" value="desbanir" class="btn-success" style="width:auto; padding:3px 8px; font-size:11px;">Desbanir</button>
                                    </form>
                                </td>
                            </tr>
                            {% endif %}
                        {% endfor %}
                    </table>
                </div>
                
                <div>
                    <h3>Chat Global (Modo Moderador)</h3>
                    <div id="chat-container"></div>
                    <input type="text" id="chat-mensagem" placeholder="Digite como Admin...">
                    
                    <div class="sticker-container">
                        <span style="font-size:12px; align-self:center;">Figurinhas:</span>
                        <button class="sticker-btn" onclick="enviarSticker('😀')">😀</button>
                        <button class="sticker-btn" onclick="enviarSticker('🔥')">🔥</button>
                        <button class="sticker-btn" onclick="enviarSticker('🚀')">🚀</button>
                        <button class="sticker-btn" onclick="enviarSticker('👍')">👍</button>
                        <button class="sticker-btn" onclick="enviarSticker('❌')">❌</button>
                    </div>

                    <button id="chat-enviar" class="btn-danger">Enviar como Admin</button>
                </div>
            </div>
            
            <a href="/">Sair do Painel</a>

            <script>
                const socket = io();
                const usuarioAtual = "{{ login }}";

                socket.on('receber_mensagem', function(dados) {
                    const chatContainer = document.getElementById('chat-container');
                    const novaMensagem = document.createElement('div');
                    novaMensagem.classList.add('msg-item');
                    const classeUser = dados.is_admin ? 'msg-admin' : 'msg-user';
                    const sufixo = dados.is_admin ? ' (Admin)' : '';
                    
                    novaMensagem.innerHTML = `
                        <span class="msg-id">ID Msg: ${dados.id}</span>
                        <span class="${classeUser}">${dados.usuario}${sufixo}:</span> ${dados.mensagem}
                    `;
                    chatContainer.appendChild(novaMensagem);
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                });

                socket.on('notificar_denuncia', function(dados) {
                    const alertaBox = document.getElementById('alerta-denuncia');
                    alertaBox.style.display = 'block';
                    alertaBox.innerHTML = `⚠️ <strong>DENÚNCIA RECEBIDA (ID: ${dados.id}):</strong> O usuário <strong>${dados.autor}</strong> denunciou <strong>${dados.alvo}</strong>. Motivo: "${dados.motivo}"`;
                });

                document.getElementById('chat-enviar').addEventListener('click', function() {
                    const campoTexto = document.getElementById('chat-mensagem');
                    const texto = campoTexto.value.trim();
                    if (texto !== '') {
                        socket.emit('enviar_mensagem', { usuario: usuarioAtual, mensagem: texto, is_admin: true });
                        campoTexto.value = '';
                    }
                });

                function enviarSticker(emoji) {
                    socket.emit('enviar_mensagem', { usuario: usuarioAtual, mensagem: emoji, is_admin: true });
                }
            </script>

        {% elif passo == 'sucesso' %}
            <h2>Sucesso</h2>
            <p class="success">Conectado como {{ login }}!</p>
            
            <hr style="margin: 20px 0; border: 0; border-top: 1px solid #ccc;">
            
            <h3>Chat Geral</h3>
            <div id="chat-container"></div>
            <input type="text" id="chat-mensagem" placeholder="Digite sua mensagem...">
            
            <div class="sticker-container">
                <span style="font-size:12px; align-self:center;">Figurinhas:</span>
                <button class="sticker-btn" onclick="enviarSticker('😀')">😀</button>
                <button class="sticker-btn" onclick="enviarSticker('🔥')">🔥</button>
                <button class="sticker-btn" onclick="enviarSticker('🚀')">🚀</button>
                <button class="sticker-btn" onclick="enviarSticker('👍')">👍</button>
                <button class="sticker-btn" onclick="enviarSticker('👑')">👑</button>
            </div>

            <button id="chat-enviar" class="btn-blue">Enviar Mensagem</button>

            <hr style="margin: 20px 0; border: 0; border-top: 1px solid #ccc;">

            <h3>Denunciar Usuário</h3>
            <div style="background: #fff3cd; padding: 10px; border-radius: 4px; border: 1px solid #ffeeba;">
                <label for="denuncia-alvo" style="font-size: 13px; font-weight: bold;">Escolha o infrator:</label>
                <select id="denuncia-alvo" style="width: 95%;">
                    {% for conta in todas_contas %}
                        {% if conta.login != login and not conta.is_admin and not conta.banido %}
                            <option value="{{ conta.login }}">{{ conta.login }}</option>
                        {% endif %}
                    {% endfor %}
                </select>
                <input type="text" id="denuncia-motivo" placeholder="Motivo da denúncia..." style="width: 90%;">
                <button id="btn-denunciar" class="btn-orange" style="width: 95%;">Enviar Denúncia</button>
                <p id="msg-denuncia-status" style="font-size: 12px; margin-top: 5px;"></p>
            </div>

            <a href="/">Sair do Chat</a>

            <script>
                const socket = io();
                const usuarioAtual = "{{ login }}";

                socket.on('receber_mensagem', function(dados) {
                    const chatContainer = document.getElementById('chat-container');
                    const novaMensagem = document.createElement('div');
                    novaMensagem.classList.add('msg-item');
                    const classeUser = dados.is_admin ? 'msg-admin' : 'msg-user';
                    const sufixo = dados.is_admin ? ' (Admin)' : '';
                    
                    novaMensagem.innerHTML = `
                        <span class="msg-id">ID Msg: ${dados.id}</span>
                        <span class="${classeUser}">${dados.usuario}${sufixo}:</span> ${dados.mensagem}
                    `;
                    chatContainer.appendChild(novaMensagem);
                    chatContainer.scrollTop = chatContainer.scrollHeight;
                });

                document.getElementById('chat-enviar').addEventListener('click', function() {
                    const campoTexto = document.getElementById('chat-mensagem');
                    const texto = campoTexto.value.trim();
                    if (texto !== '') {
                        socket.emit('enviar_mensagem', { usuario: usuarioAtual, mensagem: texto, is_admin: false });
                        campoTexto.value = '';
                    }
                });

                function enviarSticker(emoji) {
                    socket.emit('enviar_mensagem', { usuario: usuarioAtual, mensagem: emoji, is_admin: false });
                }

                document.getElementById('btn-denunciar').addEventListener('click', function() {
                    const alvo = document.getElementById('denuncia-alvo').value;
                    const motivo = document.getElementById('denuncia-motivo').value.trim();
                    const statusText = document.getElementById('msg-denuncia-status');

                    if (motivo === '') {
                        statusText.style.color = 'red';
                        statusText.innerText = 'Digite um motivo.';
                        return;
                    }

                    socket.emit('enviar_denuncia', { autor: usuarioAtual, alvo: alvo, motivo: motivo });
                    document.getElementById('denuncia-motivo').value = '';
                    statusText.style.color = 'green';
                    statusText.innerText = 'Denúncia enviada!';
                });
            </script>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, passo='login', todas_contas=contas)

@app.route('/login', methods=['POST'])
def verificar_login():
    login = request.form.get('login')
    senha = request.form.get('senha')
    
    usuario_encontrado = None
    for conta in contas:
        if conta["login"] == login and conta["senha"] == senha:
            usuario_encontrado = conta
            break
            
    if usuario_encontrado:
        if usuario_encontrado.get("banido"):
            return render_template_string(HTML_TEMPLATE, passo='login', erro="Sua conta foi BANIDA permanentemente.", todas_contas=contas)
        
        if usuario_encontrado.get("suspenso"):
            return render_template_string(HTML_TEMPLATE, passo='login', erro="Sua conta está SUSPENSA.", todas_contas=contas)
            
        if usuario_encontrado["is_admin"]:
            return render_template_string(HTML_TEMPLATE, passo='admin_painel', login=login, todas_contas=contas)
        return render_template_string(HTML_TEMPLATE, passo='sucesso', login=login, todas_contas=contas)
    else:
        return render_template_string(HTML_TEMPLATE, passo='login', erro="Acesso negado", todas_contas=contas)

@app.route('/criar_conta', methods=['POST'])
def criar_conta():
    novo_usuario = request.form.get('novo_usuario')
    nova_senha = request.form.get('nova_senha')
    
    existe = any(conta["login"] == novo_usuario for conta in contas)
    if existe:
        return render_template_string(HTML_TEMPLATE, passo='admin_painel', erro="Esse usuário já existe!", todas_contas=contas)
    
    contas.append({"login": novo_usuario, "senha": nova_senha, "is_admin": False, "suspenso": False, "banido": False})
    return render_template_string(HTML_TEMPLATE, passo='admin_painel', msg=f"Conta de '{novo_usuario}' criada!", todas_contas=contas)

@app.route('/modificar_conta', methods=['POST'])
def modificar_conta():
    usuario_alvo = request.form.get('usuario_alvo')
    acao = request.form.get('acao')
    msg_retorno = ""
    
    for conta in contas:
        if conta["login"] == usuario_alvo:
            if acao == "suspender":
                conta["suspenso"] = True
                msg_retorno = f"Usuário '{usuario_alvo}' suspenso."
            elif acao == "reativar":
                conta["suspenso"] = False
                msg_retorno = f"Usuário '{usuario_alvo}' reativado."
            elif acao == "banir":
                conta["banido"] = True
                msg_retorno = f"Usuário '{usuario_alvo}' BANIDO do sistema."
            elif acao == "desbanir":
                conta["banido"] = False
                msg_retorno = f"Usuário '{usuario_alvo}' foi DESBANIDO e agora está ativo."
            break
            
    return render_template_string(HTML_TEMPLATE, passo='admin_painel', msg=msg_retorno, todas_contas=contas)

@socketio.on('enviar_mensagem')
def (dados):
    dados['id'] = str(uuid.uuid4())[:8]
    emit('receber_mensagem', dados, broadcast=True)

@socketio.on('enviar_denuncia')
def gerenciar_denuncia(dados):
    dados['id'] = str(uuid.uuid4())[:8]
    emit('notificar_denuncia', dados, broadcast=True)
    
    # Certifique-se de ter importado o "os" no topo ou logo acima do bloco de inicialização
import os

if __name__ == '__main__':
    # Pega a porta do servidor de hospedagem ou usa 5000 como padrão local
    porta = int(os.environ.get("PORT", 5000))
    socketio.run(app, host='0.0.0.0', port=porta)
