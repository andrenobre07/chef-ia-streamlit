import streamlit as st
import google.generativeai as genai

# 1. Configurar a interface visual
st.set_page_config(page_title="Chef IA", page_icon="👨‍🍳")
st.title("👨‍🍳 Chef IA - O teu Assistente de Cozinha")
st.write("Diz-me o que tens no frigorífico e eu crio uma receita!")

# 2. Configurar a API (Funciona localmente e na Nuvem/Streamlit Cloud)
try:
    # Tenta ir buscar a chave aos Secrets do Streamlit Cloud
    CHAVE_API = st.secrets["GEMINI_API_KEY"]
except Exception:
    # Se estiveres a correr no teu PC, usa a tua chave diretamente
    CHAVE_API = "AQ.Ab8RN6LCk1yDfpkkX5VrcebcQd0rRWMO_T4XTMUalh08B-QrHg"

genai.configure(api_key=CHAVE_API)

# 3. O "System Prompt" (Instrução de personalidade de PLN)
instrucao_sistema = """
Tu és um chef de cozinha português muito simpático e focado em evitar o desperdício alimentar.
Regras:
1. Só podes responder a perguntas sobre comida, receitas e ingredientes.
2. Se o utilizador perguntar sobre outros temas (futebol, política, tempo, etc.), recusa educadamente e diz que a tua especialidade são apenas os tachos e panelas.
3. Dá respostas curtas, estruturadas e fáceis de ler (usa bullet points).
"""

# 4. Função para testar e encontrar automaticamente um modelo funcional
@st.cache_resource
def obter_modelo_funcional():
    candidatos = [
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
        "gemini-1.5-pro",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
    ]
    
    # Procura modelos adicionais associados à tua conta
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                nome = m.name.replace("models/", "")
                if nome not in candidatos and "2.5" not in nome:
                    candidatos.append(nome)
    except Exception:
        pass

    # Testa qual o primeiro modelo a responder sem erros de quota/404
    for nome_modelo in candidatos:
        try:
            m = genai.GenerativeModel(model_name=nome_modelo)
            m.generate_content("Oi")
            return nome_modelo
        except Exception:
            continue

    return "gemini-1.5-flash"

# Inicialização do Modelo e Sessão de Chat
nome_modelo_ativo = obter_modelo_funcional()

if "chat" not in st.session_state:
    modelo = genai.GenerativeModel(
        model_name=nome_modelo_ativo,
        system_instruction=instrucao_sistema
    )
    st.session_state.chat = modelo.start_chat(history=[])
    st.session_state.mensagens_ecra = [
        {"role": "assistant", "content": "Olá! Que ingredientes tens perdidos aí por casa?"}
    ]

# 5. Mostrar histórico de mensagens no ecrã
for msg in st.session_state.mensagens_ecra:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 6. Caixa de texto para o utilizador escrever
if texto_utilizador := st.chat_input("Ex: Tenho 2 ovos, queijo e tomate..."):
    
    # Mostrar a mensagem do utilizador
    with st.chat_message("user"):
        st.markdown(texto_utilizador)
    st.session_state.mensagens_ecra.append({"role": "user", "content": texto_utilizador})

    # Enviar mensagem para o Chef IA
    with st.chat_message("assistant"):
        with st.spinner("O Chef está a pensar..."):
            try:
                resposta = st.session_state.chat.send_message(texto_utilizador)
                st.markdown(resposta.text)
                st.session_state.mensagens_ecra.append({"role": "assistant", "content": resposta.text})
            except Exception as e:
                st.error(f"Erro na resposta: {e}")