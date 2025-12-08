import streamlit as st
from docx import Document
from io import BytesIO
import os
from datetime import date
import time

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Sistema HOF - Cloud", layout="wide")

# --- 2. LOGIN / SEGURANÇA ---
USUARIOS_PERMITIDOS = {
    "willians": "Re105763#",
    "paula": "Re121091"
}

def check_password():
    """Verifica se o usuário e senha estão corretos"""
    if st.session_state.get('password_correct', False):
        return True

    st.markdown("<h1 style='text-align: center;'>🔒 Acesso Restrito HOF</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        usuario = st.text_input("Usuário")
        senha = st.text_input("Senha", type="password")
        if st.button("ENTRAR", type="primary", use_container_width=True):
            if usuario in USUARIOS_PERMITIDOS and USUARIOS_PERMITIDOS[usuario] == senha:
                st.session_state['password_correct'] = True
                st.session_state['usuario_atual'] = usuario
                st.success("Login Autorizado!")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ Usuário ou Senha incorretos")
    return False

if not check_password():
    st.stop()

# --- 3. MAPEAMENTO DOS 9 PROCEDIMENTOS ---
# O sistema usa isso para achar os termos específicos (ex: termo_toxina.docx)
MAPA_ARQUIVOS = {
    "Toxina Botulínica": "toxina",
    "Preenchimento Facial": "preenchimento",
    "Bioestimulador": "bioestimulador",
    "Fios de Sustentação": "fios",
    "Lipo Mecânica de Papada": "lipomecanica",
    "Lipo Enzimática de Papada": "lipoenzimatica",
    "Bichectomia": "bichectomia",
    "Microagulhamento": "microagulhamento",
    "Peeling": "peeling"
}

# --- 4. FUNÇÕES DE AJUDA ---
def formatar_real(valor):
    """Transforma 1000.00 em 1.000,00"""
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def converter_numero_texto(dias):
    """Converte números em extenso para atestados"""
    numeros = {0: "zero", 1: "um", 2: "dois", 3: "três", 4: "quatro", 5: "cinco", 
               10: "dez", 15: "quinze", 20: "vinte", 30: "trinta"}
    return numeros.get(dias, str(dias))

def preencher_template(caminho, dados):
    """Abre o Word e troca as etiquetas pelos dados"""
    if not os.path.exists(caminho):
        return None # Retorna vazio se não achar o arquivo
    
    doc = Document(caminho)
    
    # Prepara dados calculados
    val_cheio = formatar_real(dados.get('valor_cheio', 0))
    val_desc = formatar_real(dados.get('valor_desconto', 0))
    val_final = formatar_real(dados.get('valor_final', 0))
    data_hoje = date.today().strftime("%d/%m/%Y")
    
    # Lógica do CID (Se vazio, some. Se preenchido, coloca 'CID: X')
    cid_valor = dados.get('cid', "")
    texto_cid_final = f"CID: {cid_valor}" if cid_valor else ""
    
    # --- DICIONÁRIO DE ETIQUETAS ---
    # É aqui que o sistema sabe o que trocar no Word
    refs = {
        # Pessoais
        "{{NOME_PACIENTE}}": dados.get('nome', ""),
        "{{RG_PACIENTE}}": dados.get('rg', ""),
        "{{CPF_PACIENTE}}": dados.get('cpf', ""),
        "{{CELULAR_PACIENTE}}": dados.get('celular', ""),
        "{{ENDERECO_PACIENTE}}": dados.get('endereco', ""), # Sem Ç no código
        "{{DATA_HOJE}}": data_hoje,
        
        # Procedimentos e Financeiro
        "{{DESCRIÇÃO_PROCEDIMENTOS}}": ", ".join(dados.get('procedimentos', [])), # Com Ç e ~ no código
        "{{VALOR_CHEIO}}": val_cheio,
        "{{VALOR_DESCONTO}}": val_desc,
        "{{VALOR_FINAL}}": val_final,
        "{{FORMA_PAGAMENTO}}": dados.get('pagamento', ""),
        "{{CLAUSULA_IMAGEM}}": dados.get('clausula_imagem', ""),
        
        # Clínico
        "{{LISTA_MEDICAMENTOS}}": dados.get('texto_medicamentos', ""),
        "{{DIAS_NUMERO}}": str(dados.get('dias_afastamento', 0)),
        "{{DIAS_EXTENSO}}": dados.get('dias_extenso', ""),
        "{{CID}}": texto_cid_final
    }
    
    # Faz a substituição parágrafo por parágrafo
    for p in doc.paragraphs:
        for k, v in refs.items():
            if k in p.text: 
                p.text = p.text.replace(k, v)
            
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- 5. TELA DO SISTEMA (INTERFACE) ---
with st.sidebar:
    st.success(f"🟢 Usuário: {st.session_state['usuario_atual']}")
    if st.button("Sair"):
        st.session_state['password_correct'] = False
        st.rerun()
    st.markdown("---")
    st.header("👤 Paciente")
    nome = st.text_input("Nome Completo")
    rg = st.text_input("RG")
    cpf = st.text_input("CPF")
    celular = st.text_input("Celular")
    endereco = st.text_area("Endereço")

st.title("💉 Sistema Integrado HOF")
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    procs = st.multiselect("Procedimentos Realizados", list(MAPA_ARQUIVOS.keys()))

# Lista de Opções de Documentos
opcoes_docs = [
    "Contrato de Serviço",
    "Orçamento",
    "Recibo de Pagamento",
    "Autorização Tratamento Estético",
    "Uso de Imagem",
    "Termos de Consentimento (Específicos)",
    "Cuidados Pós (Específicos)",
    "Prontuário",
    "Anamnese",
    "Receituário",
    "Atestado Médico"
]

with col2:
    docs = st.multiselect("Selecione os Documentos", opcoes_docs)

st.markdown("---")

# Variáveis para guardar os dados digitados
valor_cheio, valor_desconto, valor_final = 0.0, 0.0, 0.0
pgto, dias, dias_extenso, cid = "", 0, "", ""
txt_clausula, txt_receita = "", ""

# --- FORMULÁRIOS CONDICIONAIS ---
if docs:
    st.subheader("📝 Preenchimento de Dados")
    
    # 1. Financeiro (Aparece se escolher qualquer doc financeiro)
    financeiros = ["Contrato de Serviço", "Recibo de Pagamento", "Orçamento"]
    if any(d in docs for d in financeiros):
        st.info("💰 Dados Financeiros")
        c1, c2, c3 = st.columns(3)
        valor_cheio = c1.number_input("Valor Original (R$)", 0.0, step=50.0)
        valor_desconto = c2.number_input("Desconto (R$)", 0.0, step=50.0)
        
        valor_final = valor_cheio - valor_desconto
        c3.metric("Valor Final", f"R$ {formatar_real(valor_final)}")
        
        pgto = st.text_area("Forma de Pagamento")
        
        if valor_desconto > 0:
            txt_clausula = f"Desconto de imagem: R$ {formatar_real(valor_desconto)}."

    # 2. Receita
    if "Receituário" in docs:
        st.info("💊 Receituário")
        if 'lista_meds' not in st.session_state: st.session_state.lista_meds = []
        
        c_rem1, c_rem2 = st.columns([3, 1])
        med = c_rem1.text_input("Nome do Remédio + Posologia")
        if c_rem2.button("➕ Add") and med:
            st.session_state.lista_meds.append(med)
            
        for i, m in enumerate(st.session_state.lista_meds):
            st.text(f"{i+1}. {m}")
            txt_receita += f"{i+1}. {m}\n"
        
        if st.button("Limpar Lista"):
            st.session_state.lista_meds = []

    # 3. Atestado
    if "Atestado Médico" in docs:
        st.info("crm Atestado")
        dias = st.number_input("Dias de Afastamento", 1)
        dias_extenso = converter_numero_texto(dias)
        cid = st.text_input("CID (Opcional)")

    st.markdown("---")
    
    # --- BOTÃO GERADOR ---
    if st.button("GERAR DOCUMENTOS 📂", type="primary"):
        if not nome:
            st.error("⚠️ Por favor, preencha o Nome do Paciente.")
        else:
            # Empacota tudo num dicionário
            dados = {
                'nome': nome, 'rg': rg, 'cpf': cpf, 'celular': celular, 'endereco': endereco,
                'procedimentos': procs,
                'valor_cheio': valor_cheio, 'valor_desconto': valor_desconto, 'valor_final': valor_final,
                'pagamento': pgto, 'clausula_imagem': txt_clausula,
                'texto_medicamentos': txt_receita, 'dias_afastamento': dias, 
                'dias_extenso': dias_extenso, 'cid': cid
            }
            
            st.success("Arquivos gerados! Baixe abaixo:")

            # GERAÇÃO INDIVIDUAL DOS ARQUIVOS
            
            # Contrato Novo
            if "Contrato de Serviço" in docs:
                arq = preencher_template("templates/contrato_orofacial.docx", dados)
                if arq: st.download_button("📥 Contrato", arq, f"Contrato_{nome}.docx")
                else: st.warning("⚠️ ERRO: Arquivo 'templates/contrato_orofacial.docx' não encontrado.")

            # Orçamento Novo
            if "Orçamento" in docs:
                arq = preencher_template("templates/orcamento.docx", dados)
                if arq: st.download_button("📥 Orçamento", arq, f"Orcamento_{nome}.docx")
                else: st.warning("⚠️ ERRO: Arquivo 'templates/orcamento.docx' não encontrado.")

            # Autorização Estética Nova
            if "Autorização Tratamento Estético" in docs:
                arq = preencher_template("templates/autorizacao_estetico.docx", dados)
                if arq: st.download_button("📥 Aut. Estética", arq, f"Autorizacao_Estetico_{nome}.docx")
                else: st.warning("⚠️ ERRO: Arquivo 'templates/autorizacao_estetico.docx' não encontrado.")
            
            # Recibo
            if "Recibo de Pagamento" in docs:
                arq = preencher_template("templates/recibo.docx", dados)
                if arq: st.download_button("📥 Recibo", arq, f"Recibo_{nome}.docx")

            # Imagem
            if "Uso de Imagem" in docs:
                arq = preencher_template("templates/autorizacao_imagem.docx", dados)
                if arq: st.download_button("📥 Uso Imagem", arq, f"Imagem_{nome}.docx")

            # Prontuário e Anamnese
            if "Prontuário" in docs:
                arq = preencher_template("templates/prontuario.docx", dados)
                if arq: st.download_button("📥 Prontuário", arq, f"Prontuario_{nome}.docx")
            
            if "Anamnese" in docs:
                arq = preencher_template("templates/anamnese.docx", dados)
                if arq: st.download_button("📥 Anamnese", arq, f"Anamnese_{nome}.docx")

            # Receita e Atestado
            if "Receituário" in docs:
                arq = preencher_template("templates/receituario.docx", dados)
                if arq: st.download_button("📥 Receita", arq, f"Receita_{nome}.docx")
            
            if "Atestado Médico" in docs:
                arq = preencher_template("templates/atestado.docx", dados)
                if arq: st.download_button("📥 Atestado", arq, f"Atestado_{nome}.docx")

            # Termos Específicos (Loop)
            if "Termos de Consentimento (Específicos)" in docs:
                for proc in procs:
                    sufixo = MAPA_ARQUIVOS.get(proc)
                    nome_arq = f"termo_{sufixo}.docx"
                    arq = preencher_template(f"templates/{nome_arq}", dados)
                    if arq: st.download_button(f"📥 Termo - {proc}", arq, f"Termo_{sufixo}.docx")
                    else: st.warning(f"⚠️ ERRO: Faltou 'templates/{nome_arq}'")

            # Cuidados Pós (Loop)
            if "Cuidados Pós (Específicos)" in docs:
                for proc in procs:
                    sufixo = MAPA_ARQUIVOS.get(proc)
                    nome_arq = f"cuidados_{sufixo}.docx"
                    arq = preencher_template(f"templates/{nome_arq}", dados)
                    if arq: st.download_button(f"📥 Cuidados - {proc}", arq, f"Cuidados_{sufixo}.docx")
                    else: st.warning(f"⚠️ ERRO: Faltou 'templates/{nome_arq}'")