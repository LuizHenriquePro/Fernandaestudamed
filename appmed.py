import streamlit as st
import json
import os
import pandas as pd
import plotly.express as px
import shutil

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title=""Estudo CESAP📚",",
    page_icon="🌼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ARQUIVOS DE DADOS ---
DATA_FILE = "meu_progresso.json"
BACKUP_FILE = "meu_progresso_backup.json"

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
        "Língua Portuguesa": ["Interpretação de textos", "Tipos e gêneros", "Ortografia", "Coesão/Tempos verbais",
                              "Sintaxe/Pontuação/Crase", "Reescrita"],
        "Inglês": ["Compreensão de textos", "Gramática"],
        "Legislação": ["Controle Externo", "Legislação Institucional"],
        "Informática": ["Setor Público", "Segurança/LGPD", "Gov Digital"],
        "Raciocínio Lógico": ["Proposicional e analítica"],
        "Direito": ["Constitucional", "Administrativo"],
        "AFO": ["Administração Financeira e Orçamentária"]
    }
}


# --- FUNÇÕES DE PERSISTÊNCIA ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            if os.path.exists(BACKUP_FILE):
                with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
    return {}


def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    shutil.copy2(DATA_FILE, BACKUP_FILE)


# Inicializa o estado global
if 'progress' not in st.session_state:
    st.session_state['progress'] = load_data()

# --- INTERFACE ---

st.title("👩‍⚕️ Planner CESAP ")
st.markdown("---")

with st.sidebar:
    st.header("🌼 Menu")
    page = st.radio("Selecione:", ["📊 Dashboard", "📝 Edital Vertical", "📅 Cronograma"])
    st.markdown("---")

    st.info("💡 Seus dados são salvos automaticamente.")

    if st.button("🗑️ Limpar Tudo (CUIDADO)"):
        if st.checkbox("Confirmar exclusão definitiva?"):
            st.session_state['progress'] = {}
            save_data({})
            st.success("Dados removidos!")
            st.rerun()

# --- DASHBOARD ---
if page == "📊 Dashboard":
    st.header("📈 Seu Desempenho")

    total_topics = 0
    done_teoria = 0
    total_questoes_resolvidas = 0
    topics_com_questoes = 0

    finalizadas = []
    em_andamento = []
    faltando = []

    # Processamento para estatísticas
    for mat_cat, topicos in SYLLABUS.items():
        for nome_topico, subtopicos in topicos.items():
            total_sub = len(subtopicos)
            cont_sub_concluido = 0

            for s in subtopicos:
                total_topics += 1
                key = f"{mat_cat}-{nome_topico}-{s}"
                st_data = st.session_state['progress'].get(key, {})

                # Critério de conclusão: Teoria + Questões + Revisão marcados
                if st_data.get("teoria") and st_data.get("questoes") and st_data.get("revisao"):
                    cont_sub_concluido += 1

                if st_data.get("teoria"):
                    done_teoria += 1

                n_questoes = st_data.get("num_questoes", 0)
                total_questoes_resolvidas += n_questoes

                if st_data.get("questoes") or n_questoes > 0:
                    topics_com_questoes += 1

            label = f"{nome_topico} ({mat_cat})"
            if cont_sub_concluido == total_sub:
                finalizadas.append(label)
            elif cont_sub_concluido > 0 or any(
                    st.session_state['progress'].get(f"{mat_cat}-{nome_topico}-{s}", {}).get("teoria") for s in
                    subtopicos):
                em_andamento.append(f"{label} - {cont_sub_concluido}/{total_sub} 100%")
            else:
                faltando.append(label)

    perc_teoria = (done_teoria / total_topics * 100) if total_topics > 0 else 0

    # Cartões de Métricas
    c1, c2, c3 = st.columns(3)
    c1.metric("📌 Progresso Teoria", f"{perc_teoria:.1f}%")
    c2.metric("📖 Tópicos Lidos", f"{done_teoria}/{total_topics}")
    c3.metric("✍️ Questões Totais", f"{total_questoes_resolvidas}")

    st.progress(perc_teoria / 100)

    st.markdown("---")
    st.subheader("📋 Situação das Disciplinas")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.success(f"**Concluídas ({len(finalizadas)})**")
        for item in finalizadas: st.write(f"✅ {item}")
        if not finalizadas: st.caption("Nenhuma completa.")

    with col2:
        st.warning(f"**Iniciadas ({len(em_andamento)})**")
        for item in em_andamento: st.write(f"🚧 {item}")
        if not em_andamento: st.caption("Nenhuma iniciada.")

    with col3:
        st.error(f"**Não Tocadas ({len(faltando)})**")
        for item in faltando: st.write(f"⏳ {item}")
        if not faltando: st.caption("Todas iniciadas!")

# --- EDITAL VERTICALIZADO ---
elif page == "📝 Edital Vertical":
    st.header("📝 Edital Verticalizado")
    mat_escolhida = st.selectbox("Escolha a Matéria:", list(SYLLABUS.keys()))

    for topico, subtopicos in SYLLABUS[mat_escolhida].items():
        sub_count = len(subtopicos)
        done_t_total = 0
        done_q_total = 0
        done_r_total = 0
        q_num_total = 0

        # Checagem de progresso do grupo para o título do expander
        for s in subtopicos:
            key_check = f"{mat_escolhida}-{topico}-{s}"
            prog = st.session_state['progress'].get(key_check, {})
            if prog.get("teoria"): done_t_total += 1
            if prog.get("questoes"): done_q_total += 1
            if prog.get("revisao"): done_r_total += 1
            q_num_total += prog.get("num_questoes", 0)

        # Ícones Dinâmicos para o Grupo
        header_icons = ""
        if done_t_total == sub_count: header_icons += " 📖"
        if done_q_total == sub_count: header_icons += " ✍️"
        if done_r_total == sub_count: header_icons += " 🔄"

        # Se tudo estiver completo, substitui por um check único
        if done_t_total == sub_count and done_q_total == sub_count and done_r_total == sub_count:
            header_icons = " ✅"

        with st.expander(f"📁 {topico}{header_icons} (Total Q: {q_num_total})"):
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

                # Definir ícone individual do subtópico baseado no status
                sub_icon = "🔹"
                if status.get("teoria") and status.get("questoes") and status.get("revisao"):
                    sub_icon = "✅"
                elif status.get("teoria"):
                    sub_icon = "📖"

                cols[0].write(f"{sub_icon} {s}")

                # Checkboxes
                t = cols[1].checkbox("T", value=status.get("teoria", False), key=f"t{key}",
                                     label_visibility="collapsed")
                q = cols[2].checkbox("Q", value=status.get("questoes", False), key=f"q{key}",
                                     label_visibility="collapsed")
                r = cols[3].checkbox("R", value=status.get("revisao", False), key=f"r{key}",
                                     label_visibility="collapsed")

                # Input de número de questões
                n_q = cols[4].number_input("Nº", min_value=0, step=1, value=status.get("num_questoes", 0),
                                           key=f"nq{key}", label_visibility="collapsed")

                # Salvar alterações
                if (t, q, r, n_q) != (status.get("teoria"), status.get("questoes"), status.get("revisao"),
                                      status.get("num_questoes")):
                    st.session_state['progress'][key] = {"teoria": t, "questoes": q, "revisao": r, "num_questoes": n_q}
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
