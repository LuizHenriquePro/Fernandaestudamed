import streamlit as st
import json
import pandas as pd
import gspread
import time
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Estudo CESAP",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SOLICITA PERMISSÃO DE NOTIFICAÇÃO LOGO AO CARREGAR ---
REQUEST_PERMISSION = """
<script>
    if ('Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
    }
</script>
"""
st.markdown(REQUEST_PERMISSION, unsafe_allow_html=True)

# --- CONFIGURAÇÕES DO POMODORO ---
POMODORO_SETTINGS = {
    'som_url': 'https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3',
    'volume': 0.7,
    'vibrar': True,
    'notificacao_persistente': True
}

# --- CONEXÃO ROBUSTA COM GOOGLE SHEETS ---
@st.cache_resource
def connect_to_gsheets():
    try:
        if "gcp_service_account" not in st.secrets:
            st.error("⚠️ Secrets não configurados! Vá nas configurações do App no Streamlit Cloud.")
            return None

        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        client = gspread.authorize(creds)
        
        # --- ID DA PLANILHA ---
        SPREADSHEET_ID = "1BxiM-uQ2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z" # <--- SEU ID AQUI
        
        try:
             return client.open_by_key(SPREADSHEET_ID).sheet1
        except:
             return client.open("EstudaMed").sheet1

    except Exception as e:
        st.error(f"Erro na conexão: {e}")
        return None

SHEET = connect_to_gsheets()

# --- FUNÇÕES DE SISTEMA ---
def load_data():
    if SHEET is None: return {}
    try:
        val = SHEET.cell(1, 1).value
        return json.loads(val) if val else {}
    except:
        return {}

def save_data(data):
    if SHEET is None: return
    try:
        SHEET.update('A1', [[json.dumps(data, ensure_ascii=False)]])
    except Exception as e:
        st.warning(f"Salvando alterações... (Google Sheets)")

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
    """
    Versão otimizada para Safari com múltiplas estratégias de notificação.
    """
    notification_html = f"""
    <div id="pomodoro-alert" style="
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 30px 50px;
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        z-index: 999999;
        text-align: center;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        animation: slideIn 0.3s ease-out, pulse 2s infinite;
    ">
        <div style="font-size: 60px; margin-bottom: 10px;">🍅⏰</div>
        <h2 style="margin: 10px 0; font-size: 28px;">Pomodoro Finalizado!</h2>
        <p style="font-size: 18px; margin: 15px 0;">Você focou! Hora de fazer uma pausa 🎉</p>
        <button id="play-sound-btn" style="
            background: white;
            color: #667eea;
            border: none;
            padding: 15px 40px;
            font-size: 18px;
            font-weight: bold;
            border-radius: 50px;
            cursor: pointer;
            margin-top: 15px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
            animation: shake 0.5s infinite;
        ">🔊 Clique para Tocar Som</button>
        <button id="close-alert-btn" style="
            background: rgba(255,255,255,0.2);
            color: white;
            border: 2px solid white;
            padding: 12px 30px;
            font-size: 16px;
            border-radius: 50px;
            cursor: pointer;
            margin-top: 10px;
            margin-left: 10px;
        ">Fechar</button>
    </div>
    
    <style>
        @keyframes slideIn {{
            from {{ opacity: 0; transform: translate(-50%, -60%); }}
            to {{ opacity: 1; transform: translate(-50%, -50%); }}
        }}
        @keyframes pulse {{
            0%, 100% {{ box-shadow: 0 20px 60px rgba(0,0,0,0.3); }}
            50% {{ box-shadow: 0 20px 80px rgba(102, 126, 234, 0.6); }}
        }}
        @keyframes shake {{
            0%, 100% {{ transform: translateX(0); }}
            25% {{ transform: translateX(-5px); }}
            75% {{ transform: translateX(5px); }}
        }}
    </style>
    
    <script>
        const soundUrl = '{POMODORO_SETTINGS['som_url']}';
        const volume = {POMODORO_SETTINGS['volume']};
        let audioPlayed = false;
        
        // Função para tocar som com múltiplos fallbacks
        async function tryPlaySound() {{
            if (audioPlayed) return;
            
            try {{
                // Tenta com Audio API
                const audio = new Audio(soundUrl);
                audio.volume = volume;
                await audio.play();
                console.log('✅ Som tocado via Audio API');
                audioPlayed = true;
                return true;
            }} catch (e1) {{
                console.warn('Audio API bloqueado, tentando Web Audio...', e1);
                
                // Fallback: Web Audio API (mais confiável no Safari)
                try {{
                    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                    
                    // Carrega o som via fetch
                    const response = await fetch(soundUrl);
                    const arrayBuffer = await response.arrayBuffer();
                    const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);
                    
                    const source = audioCtx.createBufferSource();
                    const gainNode = audioCtx.createGain();
                    
                    source.buffer = audioBuffer;
                    source.connect(gainNode);
                    gainNode.connect(audioCtx.destination);
                    gainNode.gain.value = volume;
                    
                    source.start(0);
                    console.log('✅ Som tocado via Web Audio API');
                    audioPlayed = true;
                    return true;
                }} catch (e2) {{
                    console.warn('Web Audio bloqueado, usando beep...', e2);
                    
                    // Último fallback: beep sintetizado
                    try {{
                        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
                        const oscillator = audioCtx.createOscillator();
                        const gainNode = audioCtx.createGain();
                        
                        oscillator.connect(gainNode);
                        gainNode.connect(audioCtx.destination);
                        
                        oscillator.frequency.value = 800;
                        oscillator.type = 'sine';
                        gainNode.gain.setValueAtTime(0.3, audioCtx.currentTime);
                        gainNode.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.5);
                        
                        oscillator.start(audioCtx.currentTime);
                        oscillator.stop(audioCtx.currentTime + 0.5);
                        console.log('✅ Beep tocado');
                        audioPlayed = true;
                        return true;
                    }} catch (e3) {{
                        console.error('Todos os métodos de áudio falharam', e3);
                        return false;
                    }}
                }}
            }}
        }}
        
        // Tenta tocar automaticamente
        tryPlaySound().then(success => {{
            if (success) {{
                // Se conseguiu tocar, remove o modal após 3 segundos
                setTimeout(() => {{
                    document.getElementById('pomodoro-alert')?.remove();
                }}, 3000);
            }}
        }});
        
        // Botão manual
        document.getElementById('play-sound-btn').addEventListener('click', async function() {{
            const btn = this;
            const success = await tryPlaySound();
            
            if (success) {{
                btn.textContent = '✅ Som Tocado!';
                btn.style.background = '#4ade80';
                btn.style.animation = 'none';
                setTimeout(() => {{
                    document.getElementById('pomodoro-alert')?.remove();
                }}, 1500);
            }} else {{
                btn.textContent = '❌ Erro no Som';
                btn.style.background = '#ef4444';
            }}
        }});
        
        document.getElementById('close-alert-btn').addEventListener('click', function() {{
            document.getElementById('pomodoro-alert')?.remove();
        }});
        
        // Notificação
        if ('Notification' in window && Notification.permission === 'granted') {{
            try {{
                const notification = new Notification('⏰ Pomodoro Finalizado!', {{
                    body: 'Você focou! Hora de fazer uma pausa 🎉',
                    icon: 'https://em-content.zobj.net/source/apple/391/tomato_1f345.png',
                    requireInteraction: {str(POMODORO_SETTINGS['notificacao_persistente']).lower()},
                    tag: 'pomodoro-timer',
                    vibrate: {str([200, 100, 200] if POMODORO_SETTINGS['vibrar'] else []).replace("'", "")}
                }});
                
                notification.onclick = () => {{
                    window.focus();
                    tryPlaySound();
                    notification.close();
                    document.getElementById('pomodoro-alert')?.remove();
                }};
            }} catch (e) {{
                console.warn('Notificação não disponível:', e);
            }}
        }}
        
        // Auto-close após 30 segundos
        setTimeout(() => {{
            document.getElementById('pomodoro-alert')?.remove();
        }}, 30000);
        
        console.log('🍅 Pomodoro finalizado!');
        console.log('Navegador:', navigator.userAgent.includes('Safari') ? 'Safari' : 'Outro');
    </script>
    """
    
    st.markdown(notification_html, unsafe_allow_html=True)

def preload_audio_safari():
    """
    Pré-carrega áudio quando o usuário clica em START.
    Cria o contexto de interação necessário para o Safari.
    """
    preload_html = f"""
    <script>
        if (!window.pomodoroAudioPreloaded) {{
            try {{
                window.pomodoroAudio = new Audio('{POMODORO_SETTINGS['som_url']}');
                window.pomodoroAudio.volume = {POMODORO_SETTINGS['volume']};
                window.pomodoroAudio.load();
                window.pomodoroAudioPreloaded = true;
                console.log('✅ Áudio pré-carregado (contexto de interação criado)');
            }} catch (e) {{
                console.warn('Não foi possível pré-carregar:', e);
            }}
        }}
    </script>
    """
    st.markdown(preload_html, unsafe_allow_html=True)

def sync_timer():
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
        "1. Língua Portuguesa": ["1.1 Interpretação", "1.2 Tipos textuais", "1.3 Ortografia", "1.4 Coesão", 
                                 "1.5 Tempos verbais", "1.6 Morfossintaxe", "1.7 Pontuação", "1.8 Concordância",
                                 "1.9 Crase", "1.10 Pronomes", "1.11 Reescrita"],
        "2. Língua Inglesa": ["2.1 Compreensão textos", "2.2 Vocabulário", "2.3 Gramática semântica", "2.4 Inglês contemporâneo"],
        "3. Controle Externo": ["3.1 Tipos de controle", "3.2 Tribunais de Contas", "3.3 Improbidade (8.429)",
                                "3.4 Controle jurisdicional", "3.5 Controle financeiro", "3.6 Regimento TCE/RN", "3.7 Lei Orgânica TCE/RN"],
        "4. Informática": ["4.1 Cultura digital/BNCC", "4.2 Pensamento computacional", "4.3 Office", "4.4 Redes/Protocolos",
                           "4.5 Colaboração", "4.6 Segurança", "4.7 LGPD", "4.8 Gov Digital", "4.9 Sistemas públicos",
                           "4.10 IA/Big Data", "4.11 Fake news"],
        "5. Raciocínio Lógico": ["5.1 Estruturas lógicas", "5.2 Proposições", "5.3 De Morgan", "5.4 Lógica 1ª ordem",
                                 "5.5 Contagem/Probabilidade", "5.6 Conjuntos", "5.7 Problemas matriciais"],
        "6. Constitucional": ["6.1 Normas constitucionais", "6.2 Direitos fundamentais", "6.3 Organização do Estado",
                              "6.4 Poderes", "6.5 Fiscalização", "6.6 Funções essenciais"],
        "7. Administrativo": ["7.1 Organização adm.", "7.2 Atos adm.", "7.3 Agentes públicos", "7.4 Poderes",
                              "7.5 Licitação", "7.6 Controle", "7.7 Resp. Civil"],
        "8. AFO": ["8.1 Orçamento Público", "8.2 Ciclo orçamentário", "8.3 PPA/LDO/LOA", "8.4 Classificações",
                   "8.5 Execução financeira", "8.6 Receita/Despesa", "8.7 LRF", "8.8 Lei 4.320"]
    }
}

# --- INTERFACE ---
st.title("👩‍⚕️ Planner CESAP")

# Aviso para usuários Safari
st.info("""
🍎 **Usuários de Safari:** Para melhor experiência com notificações, permita em:
**Safari → Preferências → Sites → Notificações** → Permitir para este site
""", icon="🔔")

st.markdown("---")

if SHEET is None:
    st.warning("⚠️ O aplicativo não está conectado ao Google Sheets. As alterações serão perdidas ao recarregar. Verifique o ID da planilha no código.")

with st.sidebar:
    st.header("🌼 Menu")
    page = st.radio("Selecione:", ["📊 Dashboard Analytics", "📝 Edital Vertical", "📅 Cronograma"])
    st.markdown("---")

    # --- POMODORO TIMER ---
    st.subheader("🍅 Pomodoro Timer")
    
    if 'pomo_running' not in st.session_state:
        st.session_state['pomo_running'] = False
    
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

    col_p1, col_p2, col_p3 = st.columns(3)
    start_pomo = col_p1.button("▶️", help="Iniciar/Retomar")
    pause_pomo = col_p2.button("⏸️", help="Pausar")
    reset_pomo = col_p3.button("⏹️", help="Resetar")
    
    if start_pomo:
        preload_audio_safari()  # Pré-carrega áudio para Safari
        st.session_state['pomo_running'] = True
    if pause_pomo: 
        st.session_state['pomo_running'] = False
    if reset_pomo:
        st.session_state['pomo_running'] = False
        st.session_state['time_left'] = minutes * 60
        st.rerun()

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
            if not st.session_state['pomo_running']: break
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
            st.success("⏰ Tempo esgotado! Hora de descansar! 🎉")
            save_pomodoro_session(minutes)

    # --- DICAS E CONFIGURAÇÕES ---
    st.markdown("---")
    with st.expander("💡 Dicas & Configurações Safari"):
        st.markdown("""
        **🍎 Usando Safari?**
        
        Para receber alertas quando o Pomodoro terminar:
        1. ✅ Um **modal visual** aparecerá no centro da tela (sempre funciona!)
        2. 🔔 **Notificação do navegador** (se você permitiu)
        3. 🔊 Clique no botão do modal para tocar o som
        
        **Configuração ideal (Safari no Mac):**
        - Safari → Preferências → Sites → Reprodução Automática
        - Selecione "Permitir Toda Reprodução Automática"
        
        **No iPhone/iPad:**
        - Ajustes → Safari → Reprodução Automática → Permitir
        
        💡 **Dica:** Minimize a janela após iniciar o timer. Você receberá notificação!
        """)
        
        if st.button("🧪 Testar Som e Notificação"):
            play_sound()
            st.success("Alerta enviado! Se aparecer um modal, clique no botão para ouvir o som.")
    
    st.markdown("---")
    st.info("💡 Dados sincronizados com Google Sheets.")
    
    confirm_delete = st.checkbox("Desbloquear exclusão de dados")
    if confirm_delete:
        if st.button("🗑️ APAGAR TUDO AGORA", type="primary"):
            st.session_state['progress'] = {}
            save_data({})
            if 'time_left' in st.session_state: del st.session_state['time_left']
            if 'pomo_running' in st.session_state: del st.session_state['pomo_running']
            st.success("Tudo limpo!")
            time.sleep(1.5)
            st.rerun()

# --- DASHBOARD ---
if page == "📊 Dashboard Analytics":
    st.header("📈 Seu Desempenho")

    tab1, tab2, tab3 = st.tabs(["Visão Geral", "🧠 Revisão Inteligente", "📊 Gráficos Detalhados"])

    total_topics = 0
    done_teoria = 0
    total_questoes_resolvidas = 0
    chart_data = []
    finalizadas, em_andamento, faltando, revisao_items = [], [], [], []

    for mat_cat, topicos in SYLLABUS.items():
        q_count_materia = 0
        for nome_topico, subtopicos in topicos.items():
            total_sub = len(subtopicos)
            cont_sub_concluido = 0
            grupo_iniciado = False

            for s in subtopicos:
                total_topics += 1
                key = f"{mat_cat}-{nome_topico}-{s}"
                st_data = st.session_state['progress'].get(key, {})

                if st_data.get("teoria") and st_data.get("questoes") and st_data.get("revisao"):
                    cont_sub_concluido += 1
                if st_data.get("teoria"):
                    done_teoria += 1
                    grupo_iniciado = True

                n_q = st_data.get("num_questoes", 0)
                total_questoes_resolvidas += n_q
                q_count_materia += n_q
                
                if st_data.get("questoes") or n_q > 0: grupo_iniciado = True

                # Revisão
                if st_data.get("last_modified"):
                    try:
                        last_mod = datetime.fromisoformat(st_data.get("last_modified"))
                        days_diff = (datetime.now() - last_mod).days
                        if days_diff in [1, 7, 30]:
                            revisao_items.append({"Tópico": s, "Matéria": mat_cat, "Dias": days_diff})
                    except: pass

            label = f"{nome_topico} ({mat_cat})"
            if cont_sub_concluido == total_sub and total_sub > 0: finalizadas.append(label)
            elif cont_sub_concluido > 0 or grupo_iniciado: em_andamento.append(label)
            else: faltando.append(label)
        
        chart_data.append({"Matéria": mat_cat, "Questões": q_count_materia})

    perc_teoria = (done_teoria / total_topics * 100) if total_topics > 0 else 0

    with tab1:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📌 Progresso Teoria", f"{perc_teoria:.1f}%")
        c2.metric("📖 Tópicos Lidos", f"{done_teoria}/{total_topics}")
        c3.metric("✍️ Questões Totais", f"{total_questoes_resolvidas}")
        
        total_minutes_pomo = sum([s['minutes'] for s in st.session_state['progress'].get("pomodoro_sessions", [])])
        h, m = divmod(total_minutes_pomo, 60)
        c4.metric("⏱️ Tempo de Foco", f"{int(h)}h {int(m)}m")

        st.progress(perc_teoria / 100)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.success(f"**Concluídas ({len(finalizadas)})**")
            with st.container(height=300):
                for item in finalizadas: st.write(f"✅ {item}")
        with col2:
            st.warning(f"**Em Andamento ({len(em_andamento)})**")
            with st.container(height=300):
                for item in em_andamento: st.write(f"🚧 {item}")
        with col3:
            st.error(f"**Não Tocadas ({len(faltando)})**")
            with st.container(height=300):
                for item in faltando: st.write(f"⏳ {item}")

    with tab2:
        if revisao_items:
            st.table(pd.DataFrame(revisao_items))
        else:
            st.info("✅ Nenhuma revisão urgente pendente para hoje.")

        st.markdown("---")
        with st.container():
            st.markdown("### 🧠 Como funciona a Revisão Inteligente?")
            st.markdown("""
            Este sistema utiliza o conceito de **Repetição Espaçada**.
            Intervalos críticos monitorados: **1 Dia**, **7 Dias** e **30 Dias**.
            """)

    with tab3:
        if chart_data:
            df_chart = pd.DataFrame(chart_data)
            st.bar_chart(df_chart.set_index("Matéria"))

# --- EDITAL VERTICALIZADO ---
elif page == "📝 Edital Vertical":
    st.header("📝 Edital Verticalizado")
    mat_escolhida = st.selectbox("Escolha a Matéria:", list(SYLLABUS.keys()))

    for topico, subtopicos in SYLLABUS[mat_escolhida].items():
        with st.expander(f"📁 {topico}"):
            h_cols = st.columns([2.5, 0.5, 0.5, 0.5, 0.8, 0.5])
            h_cols[0].markdown("**Subtópico**")
            h_cols[1].markdown("**📖**")
            h_cols[2].markdown("**✍️**")
            h_cols[3].markdown("**🔄**")
            h_cols[4].markdown("**Qtd.**")
            h_cols[5].markdown("**Det.**")

            for s in subtopicos:
                key = f"{mat_escolhida}-{topico}-{s}"
                status = st.session_state['progress'].get(key, {})
                cols = st.columns([2.5, 0.5, 0.5, 0.5, 0.8, 0.5])
                
                sub_icon = "✅" if status.get("teoria") and status.get("questoes") and status.get("revisao") else "🔹"
                cols[0].write(f"{sub_icon} {s}")

                t = cols[1].checkbox("T", value=status.get("teoria", False), key=f"t{key}", label_visibility="collapsed")
                q = cols[2].checkbox("Q", value=status.get("questoes", False), key=f"q{key}", label_visibility="collapsed")
                r = cols[3].checkbox("R", value=status.get("revisao", False), key=f"r{key}", label_visibility="collapsed")
                n_q = cols[4].number_input("Nº", min_value=0, step=1, value=status.get("num_questoes", 0), key=f"nq{key}", label_visibility="collapsed")

                with cols[5].popover("⚙️"):
                    options_diff = ["Não avaliado", "🟢 Fácil", "🟡 Médio", "🔴 Difícil"]
                    curr_diff = status.get("dificuldade", "Não avaliado")
                    idx_diff = options_diff.index(curr_diff) if curr_diff in options_diff else 0
                    
                    new_diff = st.selectbox("Dificuldade:", options_diff, index=idx_diff, key=f"diff_{key}")
                    st.markdown("**📝 Notas:**")
                    new_note = st.text_area("Anotações", value=status.get("notes", ""), key=f"note_{key}", height=100)

                current_state = (
                    status.get("teoria"), status.get("questoes"), status.get("revisao"), 
                    status.get("num_questoes"), status.get("dificuldade"), status.get("notes")
                )
                new_state = (t, q, r, n_q, new_diff, new_note)

                if current_state != new_state:
                    st.session_state['progress'][key] = {
                        "teoria": t, "questoes": q, "revisao": r, "num_questoes": n_q,
                        "dificuldade": new_diff, "notes": new_note,
                        "last_modified": datetime.now().isoformat()
                    }
                    save_data(st.session_state['progress'])
                    st.rerun()

# --- CRONOGRAMA ---
elif page == "📅 Cronograma":
    st.header("📅 Planejamento Semanal")
    
    tab_plan, tab_history = st.tabs(["📝 Planejamento", "📊 Histórico Semanal"])
    
    with tab_plan:
        days = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
        crono_data = st.session_state['progress'].get("crono_text", {d: "" for d in days})
        
        c1, c2 = st.columns(2)
        for i, d in enumerate(days):
            with (c1 if i % 2 == 0 else c2):
                txt = st.text_area(f"📌 {d}", value=crono_data.get(d, ""), key=f"txt{d}", height=120)
                if txt != crono_data.get(d):
                    crono_data[d] = txt
                    st.session_state['progress']["crono_text"] = crono_data
                    save_data(st.session_state['progress'])
    
    with tab_history:
        st.subheader("📈 Histórico de Atividades Semanais")
        
        weekly_data = {}
        
        for mat_cat, topicos in SYLLABUS.items():
            for nome_topico, subtopicos in topicos.items():
                for s in subtopicos:
                    key = f"{mat_cat}-{nome_topico}-{s}"
                    st_data = st.session_state['progress'].get(key, {})
                    
                    if st_data.get("last_modified"):
                        has_progress = st_data.get("teoria") or st_data.get("questoes") or st_data.get("revisao") or st_data.get("num_questoes", 0) > 0
                        
                        if has_progress:
                            try:
                                last_mod = datetime.fromisoformat(st_data.get("last_modified"))
                                week_num = last_mod.isocalendar()[1]
                                year = last_mod.year
                                week_key = f"{year}-S{week_num:02d}"
                                
                                if week_key not in weekly_data:
                                    weekly_data[week_key] = {
                                        "topicos": [],
                                        "questoes": 0,
                                        "materias": set()
                                    }
                                
                                is_done = st_data.get("teoria") and st_data.get("questoes") and st_data.get("revisao")
                                status_label = "✅ Concluído" if is_done else "🚧 Em Estudo"
                                
                                weekly_data[week_key]["topicos"].append({
                                    "Matéria": mat_cat,
                                    "Subtópico": s,
                                    "Situação": status_label,
                                    "Questões": st_data.get("num_questoes", 0)
                                })
                                
                                weekly_data[week_key]["questoes"] += st_data.get("num_questoes", 0)
                                weekly_data[week_key]["materias"].add(mat_cat)
                                
                            except:
                                pass
        
        if weekly_data:
            sorted_weeks = sorted(weekly_data.items(), reverse=True)
            
            col1, col2, col3 = st.columns(3)
            total_weeks = len(sorted_weeks)
            total_questoes_hist = sum([w[1]["questoes"] for w in sorted_weeks])
            media_questoes = total_questoes_hist / total_weeks if total_weeks > 0 else 0
            
            col1.metric("📅 Semanas Ativas", total_weeks)
            col2.metric("✍️ Total de Questões", total_questoes_hist)
            col3.metric("📊 Média Questões/Semana", f"{media_questoes:.1f}")
            
            st.markdown("---")
            
            for week_key, week_info in sorted_weeks:
                num_topicos = len(week_info["topicos"])
                num_questoes = week_info["questoes"]
                materias_str = ", ".join(week_info["materias"])
                
                with st.expander(
                    f"📅 **Semana {week_key}** • {num_topicos} tópicos ativos",
                    expanded=False
                ):
                    df_week = pd.DataFrame(week_info["topicos"])
                    
                    st.dataframe(
                        df_week,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Situação": st.column_config.TextColumn(
                                "Status",
                                help="Se o tópico foi finalizado ou está em andamento",
                                validate="^✅.*"
                            ),
                            "Questões": st.column_config.NumberColumn(
                                "Questões Feitas",
                                format="%d ✍️"
                            )
                        }
                    )
                    
                    st.caption(f"Disciplinas tocadas: {materias_str}")
        else:
            st.info("📭 Nenhum histórico ainda. Seus estudos aparecerão aqui organizados por semana assim que você marcar o progresso nos checkboxes!")
