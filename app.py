import re
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

# 3. O "System Prompt" (Instrução com regra rigorosa contra rascunhos)
instrucao_sistema = """
Tu és um chef de cozinha português muito simpático e focado em evitar o desperdício alimentar.

REGRAS OBRIGATÓRIAS:
1. Responde APENAS sobre comida, receitas e ingredientes.
2. NUNCA escrevas rascunhos, planos, "User input:", "Persona:", "Rules:", "Goal:", "Drafting content:" nem blocos de pensamento.
3. Começa SEMPRE a tua resposta diretamente com a saudação ao utilizador (ex: "Olá! Com esses ingredientes...").
4. Dá respostas curtas, estruturadas e fáceis de ler (usa bullet points).
"""

# Função para filtrar e remover qualquer rascunho de pensamento/planeamento
def limpar_pensamentos(texto: str) -> str:
    # 1. Se o modelo incluir o marcador de rascunho "Drafting content:", pega apenas no texto final
    if "Drafting content:" in texto:
        texto = texto.split("Drafting content:")[-1]
    
    # 2. Remove tags <think>...</think>
    texto_limpo = re.sub(r'<think>.*?</think>', '', texto, flags=re.DOTALL)
    
    # 3. Elimina linhas que pertençam à estrutura interna de raciocínio
    prefixos_para_remover = [
        "User input:", "Persona:", "Rules:", "Goal:", "Option 1:", "Option 2:", 
        "Option 3:", "Tone:", "Structure:", "Thinking Process:", "Only food?",
        "Short/Structured?", "No internal thoughts?", "Portuguese persona?"
    ]
    
    linhas = texto_limpo.split('\n')
    linhas_finais = [
        linha for linha in linhas 
        if not any(linha.strip().startswith(p) for p in prefixos_para_remover)
    ]
    
    return '\n'.join(linhas_finais).strip()

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
                
                # Filtra e limpa o texto antes de o exibir no ecrã
                texto_final = limpar_pensamentos(resposta.text)
                
                st.markdown(texto_final)
                st.session_state.mensagens_ecra.append({"role": "assistant", "content": texto_final})
            except Exception as e:
                st.error(f"Erro na resposta: {e}")
