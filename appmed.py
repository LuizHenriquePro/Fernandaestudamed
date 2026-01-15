import streamlit as st
import json
import pandas as pd
import gspread
import time
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Estudo CESAP📚",
    page_icon="🌼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- AUTENTICAÇÃO GOOGLE SHEETS ---
# Certifique-se de que suas secrets estão configuradas corretamente no Streamlit Cloud ou localmente
try:
    SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    CREDS = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], SCOPE)
    GS_CLIENT = gspread.authorize(CREDS)
    SHEET = GS_CLIENT.open("EstudaMed").sheet1  # Nome da planilha
except Exception as e:
    st.error(f"Erro na conexão com Google Sheets: {e}")
    st.stop()

# --- FUNÇÕES DE SISTEMA ---
def load_data():
    try:
        val = SHEET.cell(1, 1).value
        return json.loads(val) if val else {}
    except Exception as e:
        # Se falhar ou estiver vazio, retorna dict vazio
        return {}

def save_data(data):
    try:
        SHEET.update('A1', [[json.dumps(data, ensure_ascii=False)]])
    except Exception as e:
        st.error(f"Erro ao salvar dados: {e}")

def save_pomodoro_session(minutes):
    if 'progress' not in st.session_state: st.session_state['progress'] = {}
    if "pomodoro_sessions" not in st.session_state['progress']:
        st.session_state['progress']["pomodoro_sessions"] = []

    session_data = {
        "date": datetime.now().isoformat(),
        "minutes": minutes
    }
    st.session_state['progress']["pomodoro_sessions"].append(session_data)
    save_data(st.session_state['progress'])

def play_sound():
    # Toca um som de notificação (beep suave)
    audio_html = """
    <audio autoplay>
    <source src="https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3" type="audio/mpeg">
    </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)

def sync_timer():
    # Sincroniza o timer quando o input muda
    st.session_state['pomo_running'] = False
    st.session_state['time_left'] = st.session_state['timer_input_value'] * 60

# Inicializa o estado global
if 'progress' not in st.session_state:
    st.session_state['progress'] = load_data()

# --- DADOS DO EDITAL ---
SYLLABUS = {
    "Medicina": {
        "1. Cuidados gerais": ["1.1 Nutrição", "1.2 Hidratação", "1.3 Prevenção câncer", "1.4 Prevenção aterosclerose"],
        "2. Doenças cardiovasculares": ["2.1 Hipertensão arterial", "2.2 Insuficiência cardíaca", "2.3 Miocardiopatias",
                                        "2.4 Valvulopatias", "2.5 Arritmias cardíacas", "2.6 Síndromes isquêmicas",
                                        "2.7 Placa aterosclerótica", "2.8 Doença coronariana crônica",
                                        "2.9 Doença arterial periférica", "2.10 Tromboembolismo venoso",
                                        "2.11 Risco cardiovascular", "2.12 Prevenção CV", "2.13 ECG básico",
                                        "2.14 Dor torácica", "2.15 Síncope"],
        "3. Doenças pulmonares": ["3.1 Asma", "3.2 DPOC", "3.3 Embolia pulmonar", "3.4 Pneumonias"],
        "4. Gastrointestinais": ["4.1 Úlcera péptica", "4.2 DRGE", "4.3 Doenças inflamatórias/parasitárias",
                                 "4.4 Diarreia", "4.5 Colelitíase", "4.6 Pancreatite", "4.7 Hepatites virais",
                                 "4.8 Insuficiência hepática", "4.9 Disabsorção"],
        "5. Urgências Comuns": ["5.1 Tontura", "5.2 Rinossinusopatias", "5.3 Urticária", "5.4 Rinite", "5.5 Cefaleias"],
        "6. Doenças Renais": ["6.1 IRA e IRC", "6.2 Glomerulonefrites", "6.3 Síndrome nefrótica", "6.4 Litíase",
                              "6.5 Ácido-base"],
        "7. Endócrinas": ["7.1 Diabetes", "7.2 Obesidade", "7.3 S. Metabólica", "7.4 Tireoide (Hipo/Hiper)",
                          "7.5 Nódulos tireoidianos", "7.6 Suprarrenais", "7.7 Paratireoides"],
        "8. Reumáticas": ["8.1 Artrite reumatoide", "8.2 Espondiloartropatias", "8.3 Colagenoses", "8.4 Gota"],
        "9. Infectologia": ["9.1 AIDS", "9.2 Endocardite", "9.3 Estafilocócicas", "9.4 Endemias nacionais",
                            "9.5 Candidíase", "9.6 DSTs", "9.7 Herpes", "9.8 Antibióticos"],
        "10. Exames": ["10.1 Invasivos e não invasivos"],
        "11. Emergências": ["11.1 Vias aéreas", "11.2 RCP", "11.3 EAP", "11.4 Crise Hipertensiva", "11.5 HDA/HDB",
                            "11.6 Choque", "11.7 Anafilaxia", "11.8 Intoxicações", "11.9 Convulsão", "11.10 AVE",
                            "11.11 Consciência", "11.12 Glicemia"],
        "12. Psiquiatria": ["12.1 Avaliação", "12.2 Ansiedade", "12.3 Depressão", "12.4 Psicose", "12.5 Bipolar",
                            "12.6 Álcool/Drogas", "12.7 Somatoformes", "12.8 Emergências Psi", "12.9 Suicídio",
                            "12.10 Psicofármacos", "12.11 Interações"],
        "13. Saúde Trabalhador": ["13.1 Doenças profissionais", "13.2 Sofrimento psíquico", "13.3 Agentes físicos",
                                  "13.4 Químicos", "13.5 Biológicos", "13.6 Ergonomia",
                                  "13.7 Trabalho noturno e em turnos", "13.8 Acidentes", "13.9 Legislação"],
        "14. Perícia": ["14.1 Conduta médico-pericial"],
        "15. Documentos Legais": ["15.1 Atestados/Laudos", "15.2 Licenças", "15.3 Bases legais"],
        "16. Conceitos Clínicos": ["16.1 Fundamentos"],
        "17. Ética": ["17.1 Ética e Bioética"],
        "18. Epidemiologia": ["18.1 Fisiopatologia geral"]
    },
    "Conhecimentos Gerais": {
    "1. Língua Portuguesa": [
        "1.1 Compreensão e interpretação de textos de gêneros variados",
        "1.2 Reconhecimento de tipos e gêneros textuais",
        "1.3 Domínio da ortografia oficial",
        "1.4 Mecanismos de coesão textual (referenciação, substituição, conectores)",
        "1.5 Emprego de tempos e modos verbais",
        "1.6 Estrutura morfossintática (classes de palavras, coordenação e subordinação)",
        "1.7 Sinais de pontuação",
        "1.8 Concordância e Regência (verbal e nominal)",
        "1.9 Sinal indicativo de crase",
        "1.10 Colocação pronominal",
        "1.11 Reescrita de frases e parágrafos (significação, substituição e reorganização)"
    ],
    "2. Língua Inglesa": [
        "2.1 Compreensão de textos (ideias principais, secundárias, explícitas e implícitas)",
        "2.2 Vocabulário e estrutura da língua",
        "2.3 Itens gramaticais para compreensão semântica",
        "2.4 Formas contemporâneas da linguagem inglesa"
    ],
    "3. Controle Externo e Legislação Institucional": [
        "3.1 Conceito, tipos e formas de controle (interno, externo, parlamentar, administrativo)",
        "3.2 Controle pelos Tribunais de Contas",
        "3.3 Lei de Improbidade Administrativa (Lei nº 8.429/1992)",
        "3.4 Sistemas de controle jurisdicional",
        "3.5 Controle da atividade financeira do Estado",
        "3.6 Regimento Interno do TCE/RN (Resolução nº 009/2012)",
        "3.7 Lei Orgânica do TCE/RN (LC nº 464/2012)"
    ],
    "4. Competências Digitais e Informática": [
        "4.1 Cultura, cidadania e letramento digital (BNCC e Lei nº 14.533/2023)",
        "4.2 Pensamento computacional e ética no uso de dados",
        "4.3 Windows e Microsoft Office (Word, Excel, PowerPoint)",
        "4.4 Redes de computadores e protocolos (TCP/IP, HTTP)",
        "4.5 Ferramentas de colaboração (Teams, Meet, E-mail)",
        "4.6 Segurança da informação (Backup, vírus, phishing, firewall)",
        "4.7 LGPD (Lei nº 13.709/2018) e Marco Civil da Internet",
        "4.8 Governo Digital (Gov.br, Portal de Dados Abertos, LAI)",
        "4.9 Sistemas do setor público (PEN, SEI, Assinatura Digital)",
        "4.10 Tecnologias emergentes (IA generativa, Big Data, IoT)",
        "4.11 Acessibilidade e combate a fake news"
    ],
    "5. Raciocínio Lógico": [
        "5.1 Estruturas lógicas e lógica de argumentação",
        "5.2 Lógica sentencial (Proposições, Tabelas-verdade, Equivalências)",
        "5.3 Leis de De Morgan e Diagramas lógicos",
        "5.4 Lógica de primeira ordem",
        "5.5 Princípios de contagem e probabilidade",
        "5.6 Operações com conjuntos",
        "5.7 Problemas aritméticos, geométricos e matriciais"
    ],
    "6. Noções de Direito Constitucional": [
        "6.1 Aplicabilidade das normas constitucionais (Eficácia e normas programáticas)",
        "6.2 Direitos e garantias fundamentais",
        "6.3 Organização político-administrativa do Estado",
        "6.4 Poder Executivo, Legislativo e Judiciário",
        "6.5 Fiscalização contábil, financeira e orçamentária",
        "6.6 Funções essenciais à justiça"
    ],
    "7. Noções de Direito Administrativo": [
        "7.1 Organização administrativa (Direta, Indireta, Descentralização)",
        "7.2 Atos administrativos (Conceito, requisitos e atributos)",
        "7.3 Agentes públicos e disposições constitucionais",
        "7.4 Poderes administrativos e uso/abuso de poder",
        "7.5 Licitação (Lei Geral, modalidades e contratação direta)",
        "7.6 Controle da administração pública",
        "7.7 Responsabilidade civil do Estado"
    ],
    "8. Administração Financeira e Orçamentária (AFO)": [
        "8.1 Orçamento Público (Conceito, técnicas e princípios)",
        "8.2 Ciclo e Processo orçamentário",
        "8.3 Instrumentos de planejamento (PPA, LDO, LOA)",
        "8.4 Classificações orçamentárias e Créditos adicionais",
        "8.5 Programação e execução financeira",
        "8.6 Receita e Despesa Pública (Conceitos, estágios e restos a pagar)",
        "8.7 Lei de Responsabilidade Fiscal (LC nº 101/2000)",
        "8.8 Lei nº 4.320/1964"]
    }
}

# --- INTERFACE ---
st.title("👩‍⚕️ Planner CESAP Pro (Google Cloud)")
st.markdown("---")

with st.sidebar:
    st.header("🌼 Menu")
    page = st.radio("Selecione:", ["📊 Dashboard", "📝 Edital Vertical", "📅 Cronograma"])
    st.markdown("---")

    # --- POMODORO TIMER APERFEIÇOADO (COM SOM E PAUSA) ---
    st.subheader("🍅 Pomodoro Timer")
    
    # Inicialização das variáveis do timer
    if 'pomo_running' not in st.session_state:
        st.session_state['pomo_running'] = False
    
    # Input do tempo (Com Callback on_change para sincronia imediata)
    minutes = st.number_input(
        "Minutos de foco:", 
        min_value=1, 
        max_value=120, 
        value=25, 
        step=5,
        key='timer_input_value',
        on_change=sync_timer
    )
    
    if 'time_left' not in st.session_state:
        st.session_state['time_left'] = minutes * 60

    # Botões de Controle
    col_p1, col_p2, col_p3 = st.columns(3)
    
    start_pomo = col_p1.button("▶️", help="Iniciar/Retomar")
    pause_pomo = col_p2.button("⏸️", help="Pausar")
    reset_pomo = col_p3.button("⏹️", help="Resetar")
    
    # Lógica dos Botões
    if start_pomo:
        st.session_state['pomo_running'] = True
    
    if pause_pomo:
        st.session_state['pomo_running'] = False
        
    if reset_pomo:
        st.session_state['pomo_running'] = False
        st.session_state['time_left'] = minutes * 60
        st.rerun()

    # Mostrador Visual e Loop
    timer_placeholder = st.empty()
    progress_bar = st.progress(0)
    
    mins, secs = divmod(st.session_state['time_left'], 60)
    timer_placeholder.metric("Tempo", f"{mins:02d}:{secs:02d}")
    
    total_sec_ref = minutes * 60
    if total_sec_ref > 0:
        curr_prog = 1 - (st.session_state['time_left'] / total_sec_ref)
        progress_bar.progress(min(max(curr_prog, 0.0), 1.0))

    if st.session_state['pomo_running']:
        while st.session_state['time_left'] > 0:
            if not st.session_state['pomo_running']:
                break
            
            st.session_state['time_left'] -= 1
            
            mins, secs = divmod(st.session_state['time_left'], 60)
            timer_placeholder.metric("Tempo", f"{mins:02d}:{secs:02d}")
            
            curr_prog = 1 - (st.session_state['time_left'] / total_sec_ref)
            progress_bar.progress(min(max(curr_prog, 0.0), 1.0))
            
            time.sleep(1)
        
        if st.session_state['time_left'] == 0 and st.session_state['pomo_running']:
            st.session_state['pomo_running'] = False
            play_sound()
            st.balloons()
            st.success("Tempo esgotado!")
            save_pomodoro_session(minutes)

    st.markdown("---")
    st.info("💡 Seus dados são salvos no Google Sheets.")

    # --- BOTÃO DE LIMPEZA SEGURO ---
    confirm_delete = st.checkbox("Desbloquear exclusão de dados")
    if confirm_delete:
        if st.button("🗑️ APAGAR TUDO AGORA", type="primary"):
            st.session_state['progress'] = {}
            save_data({}) # Limpa no Google Sheets
            
            # Limpa estados visuais
            if 'time_left' in st.session_state: del st.session_state['time_left']
            if 'pomo_running' in st.session_state: del st.session_state['pomo_running']
            
            st.success("Dados removidos!")
            time.sleep(1.5)
            st.rerun()

# --- DASHBOARD ---
if page == "📊 Dashboard":
    st.header("📈 Seu Desempenho")

    total_topics = 0
    done_teoria = 0
    total_questoes_resolvidas = 0

    finalizadas = []
    em_andamento = []
    faltando = []

    for mat_cat, topicos in SYLLABUS.items():
        for nome_topico, subtopicos in topicos.items():
            total_sub = len(subtopicos)
            cont_sub_concluido = 0

            # Verifica progresso do grupo
            grupo_iniciado = False

            for s in subtopicos:
                total_topics += 1
                key = f"{mat_cat}-{nome_topico}-{s}"
                st_data = st.session_state['progress'].get(key, {})

                if st_data.get("teoria") and st_data.get("questoes") and st_data.get("revisao"):
                    cont_sub_concluido += 1
                
                if st_data.get("teoria") or st_data.get("questoes") or st_data.get("num_questoes", 0) > 0:
                    grupo_iniciado = True

                if st_data.get("teoria"):
                    done_teoria += 1
                total_questoes_resolvidas += st_data.get("num_questoes", 0)

            label = f"{nome_topico} ({mat_cat})"
            if cont_sub_concluido == total_sub and total_sub > 0:
                finalizadas.append(label)
            elif cont_sub_concluido > 0 or grupo_iniciado:
                percentual = int((cont_sub_concluido / total_sub) * 100) if total_sub > 0 else 0
                em_andamento.append(f"{label} - {percentual}%")
            else:
                faltando.append(label)

    perc_teoria = (done_teoria / total_topics * 100) if total_topics > 0 else 0

    # Cartões de Métricas
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📌 Progresso Teoria", f"{perc_teoria:.1f}%")
    c2.metric("📖 Tópicos Lidos", f"{done_teoria}/{total_topics}")
    c3.metric("✍️ Questões Totais", f"{total_questoes_resolvidas}")

    # Cálculo de Horas Estudadas (Baseado no Pomodoro)
    total_minutes_pomo = sum([s['minutes'] for s in st.session_state['progress'].get("pomodoro_sessions", [])])
    hours_studied, mins_studied = divmod(total_minutes_pomo, 60)
    c4.metric("⏱️ Tempo de Foco", f"{int(hours_studied)}h {int(mins_studied)}m")

    st.progress(perc_teoria / 100)

    st.markdown("---")
    st.subheader("📋 Situação das Disciplinas")
    
    # Listas com Scroll (st.container)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.success(f"**Concluídas ({len(finalizadas)})**")
        with st.container(height=300):
            if not finalizadas:
                st.caption("Continue estudando!")
            else:
                for item in finalizadas: st.write(f"✅ {item}")
    
    with col2:
        st.warning(f"**Iniciadas ({len(em_andamento)})**")
        with st.container(height=300):
            if not em_andamento:
                st.caption("Nada em andamento.")
            else:
                for item in em_andamento: st.write(f"🚧 {item}")
    
    with col3:
        st.error(f"**Não Tocadas ({len(faltando)})**")
        with st.container(height=300):
            if not faltando:
                st.write("Todas iniciadas! 🚀")
            else:
                for item in faltando: st.write(f"⏳ {item}")

# --- EDITAL VERTICALIZADO ---
elif page == "📝 Edital Vertical":
    st.header("📝 Edital Verticalizado")
    mat_escolhida = st.selectbox("Escolha a Matéria:", list(SYLLABUS.keys()))

    for topico, subtopicos in SYLLABUS[mat_escolhida].items():
        with st.expander(f"📁 {topico}"):
            h_cols = st.columns([2.5, 0.8, 0.8, 0.8, 1.2])
            h_cols[0].markdown("**Subtópico**")
            h_cols[1].markdown("**📖 Teoria**")
            h_cols[2].markdown("**✍️ Questões**")
            h_cols[3].markdown("**🔄 Rev**")
            h_cols[4].markdown("**Qtd Questões**")

            for s in subtopicos:
                key = f"{mat_escolhida}-{topico}-{s}"
                status = st.session_state['progress'].get(key, {})
                cols = st.columns([2.5, 0.8, 0.8, 0.8, 1.2])
                
                sub_icon = "✅" if status.get("teoria") and status.get("questoes") and status.get("revisao") else "🔹"
                cols[0].write(f"{sub_icon} {s}")
                
                t = cols[1].checkbox("T", value=status.get("teoria", False), key=f"t{key}", label_visibility="collapsed")
                q = cols[2].checkbox("Q", value=status.get("questoes", False), key=f"q{key}", label_visibility="collapsed")
                r = cols[3].checkbox("R", value=status.get("revisao", False), key=f"r{key}", label_visibility="collapsed")
                n_q = cols[4].number_input("Nº", min_value=0, step=1, value=status.get("num_questoes", 0), key=f"nq{key}", label_visibility="collapsed")

                # Verifica mudança e Salva
                if (t, q, r, n_q) != (status.get("teoria"), status.get("questoes"), status.get("revisao"), status.get("num_questoes")):
                    st.session_state['progress'][key] = {
                        "teoria": t, 
                        "questoes": q, 
                        "revisao": r, 
                        "num_questoes": n_q,
                        "last_modified": datetime.now().isoformat() # Adiciona timestamp para futuros analytics
                    }
                    save_data(st.session_state['progress'])
                    st.rerun()

# --- CRONOGRAMA ---
elif page == "📅 Cronograma":
    st.header("📅 Planejamento Semanal")
    days = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    crono_data = st.session_state['progress'].get("crono_text", {d: "" for d in days})
    
    c1, c2 = st.columns(2)
    for i, d in enumerate(days):
        target_col = c1 if i % 2 == 0 else c2
        with target_col:
            txt = st.text_area(f"📌 {d}", value=crono_data.get(d, ""), key=f"txt{d}", height=120)
            if txt != crono_data.get(d):
                crono_data[d] = txt
                st.session_state['progress']["crono_text"] = crono_data
                save_data(st.session_state['progress'])
