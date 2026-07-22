import streamlit as st
import google.generativeai as genai

# 1. Configurar a interface visual
st.set_page_config(page_title="Chef IA", page_icon="👨‍🍳")

# Título Principal e Membros do Grupo
st.title("👨‍🍳 Chef IA - O teu Assistente de Cozinha")
st.caption("Trabalho desenvolvido por: **André Nobre**, **Diogo Ramiro** e **Rodrigo Gomes**")
st.write("Diz-me o que tens no frigorífico e eu crio uma receita!")

# Barra Lateral (Sidebar) com informação do projeto
with st.sidebar:
    st.header("👥 Grupo de Trabalho")
    st.write("• **André Nobre**")
    st.write("• **Diogo Ramiro**")
    st.write("• **Rodrigo Gomes**")
    st.markdown("---")
    st.caption("Projeto de Inteligência Artificial")

# 2. Configurar a API em segurança via Secrets
if "GEMINI_API_KEY" in st.secrets:
    CHAVE_API = str(st.secrets["GEMINI_API_KEY"]).strip().replace('"', '').replace("'", "")
    genai.configure(api_key=CHAVE_API)
else:
    st.error("⚠️ A chave da API não foi encontrada nos Secrets do Streamlit!")
    st.stop()

# 3. O "System Prompt" (Direto e sem desencadear autoanálises em inglês)
instrucao_sistema = """
Tu és o Chef IA, um chef de cozinha português muito simpático e focado em evitar o desperdício alimentar.

Directrizes:
- Responde APENAS sobre culinária, receitas e aproveitamento de ingredientes.
- Começa SEMPRE a tua resposta com uma saudação simpática em português (ex: "Olá!").
- Dá sugestões práticas e organizadas em tópicos (bullet points).
- Responde diretamente ao utilizador sem acrescentar notas técnicas ou análises.
"""

# Função que isola a resposta final e elimina todo o raciocínio/rascunhos em inglês
def limpar_pensamentos(texto: str) -> str:
    # Se o modelo gerou a secção "Revised Version:", extrai o conteúdo a partir daí
    if "Revised Version:" in texto:
        texto = texto.split("Revised Version:")[-1]
    
    # A resposta final do Chef começa sempre pela saudação "Olá"
    if "Olá" in texto:
        partes = texto.split("Olá")
        return ("Olá" + partes[-1]).strip()
    
    # Filtro secundário de segurança para termos de raciocínio
    termos_lixo = [
        "User input:", "Role:", "Constraints:", "Goal:", "Option 1:", "Option 2:", 
        "Option 3:", "Greeting:", "Structure:", "Does it meet", "Only food?",
        "No meta-text?", "Starts with greeting?", "Short/structured?",
        "Drafting content:", "(Wait,", "(I should", "Thinking Process:"
    ]
    
    linhas = [l for l in texto.split('\n') if not any(t in l for t in termos_lixo)]
    return '\n'.join(linhas).strip()

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
    
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                nome = m.name.replace("models/", "")
                if nome not in candidatos and "2.5" not in nome:
                    candidatos.append(nome)
    except Exception:
        pass

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
    
    with st.chat_message("user"):
        st.markdown(texto_utilizador)
    st.session_state.mensagens_ecra.append({"role": "user", "content": texto_utilizador})

    with st.chat_message("assistant"):
        with st.spinner("O Chef está a pensar..."):
            try:
                resposta = st.session_state.chat.send_message(texto_utilizador)
                
                # Extrai limpa e exclusivamente a resposta final
                texto_final = limpar_pensamentos(resposta.text)
                
                st.markdown(texto_final)
                st.session_state.mensagens_ecra.append({"role": "assistant", "content": texto_final})
            except Exception as e:
                st.error(f"Erro na resposta: {e}")
