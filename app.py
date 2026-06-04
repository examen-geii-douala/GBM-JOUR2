import time
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

import gspread
from google.oauth2.service_account import Credentials

# ============================================================
# CONFIG
# ============================================================
SESSION = "GBM_2026-06-04_jour2"
DUREE = 10 * 60  # 10 minutes
CODE_ADMIN = "GBM2024"  # change si tu veux

st.set_page_config(page_title="Maintenance biomédicale avancée", layout="centered")

# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
.big-title{ text-align:center;color:#1e3a8a;font-size:26px;font-weight:800;margin-top:6px;}
.sub-title{ text-align:center;color:#dc2626;font-size:18px;margin-bottom:10px;}
.timer-box{ text-align:center;font-size:46px;color:#dc2626;font-weight:900;padding:10px;border:4px solid #dc2626;border-radius:14px;background:#fff1f2;margin:10px 0;}
.info-box{ background:#eff6ff;padding:12px;border-radius:10px;border-left:5px solid #1e40af;margin:10px 0;}
.section-title{ color:#1e40af;font-size:19px;font-weight:800;margin-top:6px;}
</style>
""", unsafe_allow_html=True)

# ============================================================
# QUESTIONS (30) + BONNES REPONSES
# ============================================================
QUESTIONS = [
    ("Q1. Lors d’une maintenance préventive d’un respirateur, quelle opération est prioritaire ?", [
        "Remplacement systématique de tous les composants",
        "Vérification des alarmes et de la précision des paramètres ventilatoires",
        "Nettoyage externe uniquement",
        "Mise à jour du dossier patient"
    ]),
    ("Q2. Le calcul du taux de disponibilité d’un équipement est :", [
        "Temps de fonctionnement / Temps total × 100",
        "Temps de panne / Temps total × 100",
        "Nombre de réparations / Nombre de pannes",
        "MTTR / MTBF"
    ]),
    ("Q3. Une augmentation du MTTR indique :", [
        "Une amélioration de la maintenance",
        "Une diminution du temps de réparation",
        "Un allongement du temps moyen de réparation",
        "Une augmentation du MTBF"
    ]),
    ("Q4. Quel indicateur est le plus pertinent pour évaluer la fiabilité d’un dispositif médical ?", [
        "MTBF",
        "Tension nominale",
        "Puissance absorbée",
        "Poids"
    ]),
    ("Q5. Une maintenance conditionnelle est déclenchée :", [
        "À date fixe",
        "Après panne",
        "Selon l’état réel de l’équipement",
        "À la demande du patient"
    ]),

    ("Q6. Lors du contrôle qualité d’un défibrillateur, l’énergie délivrée mesurée est de 190 J pour une consigne de 200 J. L’équipement est :", [
        "Nécessairement conforme",
        "Nécessairement non conforme",
        "Conforme ou non selon les tolérances du fabricant",
        "Hors service"
    ]),
    ("Q7. La traçabilité métrologique exige :", [
        "Une chaîne ininterrompue d’étalonnages reliée à des références nationales ou internationales",
        "Une calibration annuelle uniquement",
        "Une maintenance mensuelle",
        "Une certification ISO 9001"
    ]),
    ("Q8. L’incertitude de mesure représente :", [
        "Une erreur de l’opérateur",
        "Un intervalle dans lequel se situe probablement la valeur vraie",
        "Une panne de l’appareil",
        "Une dérive systématique"
    ]),
    ("Q9. Quel instrument est le plus adapté pour vérifier la précision d’un tensiomètre ?", [
        "Simulateur de pression non invasive",
        "ECG",
        "Multimètre",
        "Oscilloscope"
    ]),
    ("Q10. Une dérive progressive d’un capteur est généralement détectée grâce :", [
        "Aux contrôles qualité périodiques",
        "Aux réparations correctives",
        "Aux inventaires",
        "À la stérilisation"
    ]),

    ("Q11. Selon le MDR 2017/745, quel dispositif présente généralement le niveau de risque le plus élevé ?", [
        "Classe I",
        "Classe IIa",
        "Classe IIb",
        "Classe III"
    ]),
    ("Q12. Un stimulateur cardiaque implantable appartient généralement à :", [
        "Classe I",
        "Classe IIa",
        "Classe IIb",
        "Classe III"
    ]),
    ("Q13. L’objectif principal du système UDI est :", [
        "Réduire le coût des dispositifs",
        "Assurer l’identification et la traçabilité des dispositifs médicaux",
        "Améliorer la qualité d’image",
        "Réduire la consommation électrique"
    ]),
    ("Q14. Après la mise sur le marché, le fabricant doit assurer :", [
        "La surveillance après commercialisation (PMS)",
        "La maintenance hospitalière",
        "La gestion du personnel",
        "La stérilisation"
    ]),
    ("Q15. Quel document décrit l’analyse des risques d’un dispositif médical ?", [
        "Dossier de gestion des risques",
        "Facture d’achat",
        "Bon de livraison",
        "Manuel utilisateur uniquement"
    ]),

    ("Q16. L’IRM produit des images grâce :", [
        "Aux rayons X",
        "Aux ultrasons",
        "À un champ magnétique intense et aux radiofréquences",
        "À la lumière infrarouge"
    ]),
    ("Q17. Le principal danger associé à l’IRM est :", [
        "Les ultrasons",
        "L’attraction d’objets ferromagnétiques",
        "Le manque d’oxygène",
        "Les UV"
    ]),
    ("Q18. Dans un ECG standard, combien d’électrodes sont utilisées pour obtenir 12 dérivations ?", [
        "4",
        "6",
        "10",
        "12"
    ]),
    ("Q19. L’effet Doppler en échographie permet :", [
        "La mesure des flux sanguins",
        "La mesure de la glycémie",
        "La mesure de la température",
        "La mesure de la pression intracrânienne"
    ]),
    ("Q20. La grandeur principale surveillée par un oxymètre est :", [
        "SpO₂",
        "ECG",
        "EEG",
        "EMG"
    ]),

    ("Q21. Un moniteur multiparamétrique affiche une saturation de 50 % alors que le patient est conscient et stable. La première action du technicien biomédical est :", [
        "Remplacer immédiatement le moniteur",
        "Vérifier le capteur et son positionnement",
        "Arrêter le service",
        "Changer la batterie du patient"
    ]),
    ("Q22. Une pompe à perfusion délivre 120 mL/h alors que la consigne est de 100 mL/h. Le risque principal est :", [
        "Sous-dosage",
        "Surdosage médicamenteux",
        "Perte d’alimentation",
        "Décharge électrostatique"
    ]),
    ("Q23. Lors d’un contrôle de sécurité électrique, un courant de fuite supérieur à la limite autorisée est observé. L’action appropriée est :", [
        "Maintenir l’équipement en service",
        "Retirer l’équipement du service jusqu’à correction",
        "Ignorer le résultat",
        "Réinitialiser l’appareil"
    ]),
    ("Q24. Quel équipement est considéré comme critique pour la survie immédiate du patient ?", [
        "Balance électronique",
        "Tensiomètre manuel",
        "Ventilateur de réanimation",
        "Thermomètre"
    ]),
    ("Q25. Dans une GMAO, un équipement ayant des pannes répétitives doit :", [
        "Faire l’objet d’une analyse de causes racines",
        "Être ignoré",
        "Être déplacé dans un autre service",
        "Être utilisé davantage"
    ]),
    ("Q26. Quel paramètre est le plus important pour la maintenance d’un scanner CT ?", [
        "Température de la salle uniquement",
        "Performance du tube à rayons X",
        "Couleur du logiciel",
        "Nombre d’utilisateurs"
    ]),
    ("Q27. La norme IEC 60601 traite principalement :", [
        "La sécurité électrique et les performances essentielles des équipements électromédicaux",
        "La qualité de l’air",
        "Les réseaux GSM",
        "Les bâtiments hospitaliers"
    ]),
    ("Q28. Un incident ayant causé un décès lié à un dispositif médical doit être :", [
        "Documenté uniquement",
        "Signalé dans le cadre de la matériovigilance",
        "Archivé sans action",
        "Ignoré"
    ]),
    ("Q29. Le principal avantage d’une maintenance basée sur la fiabilité (RCM) est :", [
        "Réduire les interventions inutiles tout en maintenant la sécurité",
        "Supprimer la maintenance préventive",
        "Réduire le nombre de techniciens",
        "Éliminer toutes les pannes"
    ]),
    ("Q30. Lorsqu’un défibrillateur est utilisé sur un patient, quelle vérification doit être effectuée après utilisation ?", [
        "Contrôle fonctionnel et recharge complète de la batterie",
        "Changement du boîtier",
        "Remplacement systématique des cartes électroniques",
        "Reprogrammation du patient"
    ]),
]

BONNES = {
    "Q1": "Vérification des alarmes et de la précision des paramètres ventilatoires",
    "Q2": "Temps de fonctionnement / Temps total × 100",
    "Q3": "Un allongement du temps moyen de réparation",
    "Q4": "MTBF",
    "Q5": "Selon l’état réel de l’équipement",
    "Q6": "Conforme ou non selon les tolérances du fabricant",
    "Q7": "Une chaîne ininterrompue d’étalonnages reliée à des références nationales ou internationales",
    "Q8": "Un intervalle dans lequel se situe probablement la valeur vraie",
    "Q9": "Simulateur de pression non invasive",
    "Q10": "Aux contrôles qualité périodiques",
    "Q11": "Classe III",
    "Q12": "Classe III",
    "Q13": "Assurer l’identification et la traçabilité des dispositifs médicaux",
    "Q14": "La surveillance après commercialisation (PMS)",
    "Q15": "Dossier de gestion des risques",
    "Q16": "À un champ magnétique intense et aux radiofréquences",
    "Q17": "L’attraction d’objets ferromagnétiques",
    "Q18": "10",
    "Q19": "La mesure des flux sanguins",
    "Q20": "SpO₂",
    "Q21": "Vérifier le capteur et son positionnement",
    "Q22": "Surdosage médicamenteux",
    "Q23": "Retirer l’équipement du service jusqu’à correction",
    "Q24": "Ventilateur de réanimation",
    "Q25": "Faire l’objet d’une analyse de causes racines",
    "Q26": "Performance du tube à rayons X",
    "Q27": "La sécurité électrique et les performances essentielles des équipements électromédicaux",
    "Q28": "Signalé dans le cadre de la matériovigilance",
    "Q29": "Réduire les interventions inutiles tout en maintenant la sécurité",
    "Q30": "Contrôle fonctionnel et recharge complète de la batterie",
}

# ============================================================
# GOOGLE SHEETS
# ============================================================
def _gs_client():
    sheet_id = st.secrets["SHEET_ID"]
    info = dict(st.secrets["google"])
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(sheet_id)
    ws = sh.worksheet("DATA")
    return ws

@st.cache_resource
def get_ws():
    return _gs_client()

def sheet_has_attempt(ws, session: str, matricule: str) -> bool:
    values = ws.get_all_values()
    if len(values) <= 1:
        return False
    header = values[0]
    i_session = header.index("session")
    i_matricule = header.index("matricule")
    for row in values[1:]:
        if len(row) > max(i_session, i_matricule):
            if row[i_session].strip() == session and row[i_matricule].strip() == matricule:
                return True
    return False

def append_attempt(ws, row: list):
    ws.append_row(row, value_input_option="RAW")

def compute_score(answer_map: dict) -> tuple[int, float]:
    score = 0
    for q, bonne in BONNES.items():
        if answer_map.get(q) == bonne:
            score += 1
    sur20 = round((score / 30) * 20, 2)
    return score, sur20

# ============================================================
# STATE
# ============================================================
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "tab_switch_count" not in st.session_state:
    st.session_state.tab_switch_count = 0
if "auto_close" not in st.session_state:
    st.session_state.auto_close = False

for i in range(1, 31):
    k = f"r{i}"
    if k not in st.session_state:
        st.session_state[k] = None

# ============================================================
# HEADER
# ============================================================
st.markdown("<div class='big-title'>Maintenance biomédicale avancée</div>", unsafe_allow_html=True)
st.markdown(f"<div class='sub-title'>Session : {SESSION} — STRICT anti-triche</div>", unsafe_allow_html=True)
st.markdown("---")

# ============================================================
# ANTI-CHEAT (STRICT)
# ============================================================
anti_cheat = components.html(
    """
    <script>
    const KEY = "tab_switch_count";
    function inc(){
        let v = parseInt(localStorage.getItem(KEY) || "0");
        v = v + 1;
        localStorage.setItem(KEY, String(v));
        window.parent.postMessage({isStreamlitMessage: true, type: "streamlit:setComponentValue", value: {tab_switch_count: v}}, "*");
    }
    document.addEventListener("visibilitychange", () => { if (document.hidden) inc(); });
    window.addEventListener("blur", () => { inc(); });
    let init = parseInt(localStorage.getItem(KEY) || "0");
    window.parent.postMessage({isStreamlitMessage: true, type: "streamlit:setComponentValue", value: {tab_switch_count: init}}, "*");
    </script>
    """,
    height=0,
)

if isinstance(anti_cheat, dict) and "tab_switch_count" in anti_cheat:
    st.session_state.tab_switch_count = int(anti_cheat["tab_switch_count"])

if st.session_state.start_time is not None and (not st.session_state.submitted):
    if st.session_state.tab_switch_count >= 1:
        st.session_state.auto_close = True

# ============================================================
# IDENTIFICATION
# ============================================================
if st.session_state.start_time is None and not st.session_state.submitted:
    st.markdown(
        "<div class='info-box'>"
        "<b>Consignes :</b><br>"
        "- Une seule tentative par <b>matricule</b> (par session).<br>"
        "- Si vous quittez la page / changez d’onglet / arrière-plan : <b>soumission immédiate</b>.<br>"
        "</div>",
        unsafe_allow_html=True
    )

    with st.form("identification"):
        nom = st.text_input("Nom et prénom *")
        matricule = st.text_input("Matricule *")
        etablissement = st.text_input("Établissement *", value="IUT de Douala")
        start = st.form_submit_button("🚀 COMMENCER", use_container_width=True)

        if start:
            nom = nom.strip()
            matricule = matricule.strip()
            etablissement = etablissement.strip()

            if not (nom and matricule and etablissement):
                st.error("Tous les champs sont obligatoires.")
                st.stop()

            ws = get_ws()
            if sheet_has_attempt(ws, SESSION, matricule):
                st.error("❌ Personne existante déjà / tentative déjà utilisée pour ce matricule (session en cours).")
                st.stop()

            st.session_state.nom = nom
            st.session_state.matricule = matricule
            st.session_state.etablissement = etablissement
            st.session_state.start_time = time.time()
            st.rerun()

# ============================================================
# FIN
# ============================================================
elif st.session_state.submitted:
    st.success("✅ Examen soumis. Vous pouvez fermer la page.")
    st.stop()

# ============================================================
# EXAM
# ============================================================
else:
    elapsed = time.time() - st.session_state.start_time
    remaining = DUREE - elapsed
    if remaining < 0:
        remaining = 0

    m, s = divmod(int(remaining), 60)
    st.markdown(f"<div class='timer-box'>⏱️ {m:02d}:{s:02d}</div>", unsafe_allow_html=True)

    st.markdown(
        f"<div class='info-box'>"
        f"👤 <b>{st.session_state.nom}</b> — 🆔 <b>{st.session_state.matricule}</b><br>"
        f"🏫 {st.session_state.etablissement}<br>"
        f"🛑 Sorties détectées : <b>{st.session_state.tab_switch_count}</b> (STRICT)"
        f"</div>",
        unsafe_allow_html=True
    )

    def qcm(i: int, label: str, options: list[str]):
        return st.radio(label, options, index=None, key=f"r{i}")

    with st.form("exam_form"):
        st.markdown("<div class='section-title'>Maintenance biomédicale avancée</div>", unsafe_allow_html=True)
        for i in range(1, 31):
            label, opts = QUESTIONS[i - 1]
            qcm(i, label, opts)

        st.markdown("---")
        submit_btn = st.form_submit_button("📩 SOUMETTRE", use_container_width=True)

    must_submit = submit_btn or (remaining <= 0) or st.session_state.auto_close

    if must_submit:
        answer_map = {f"Q{i}": st.session_state.get(f"r{i}") for i in range(1, 31)}
        score_raw, score_sur20 = compute_score(answer_map)

        was_auto_closed = "YES" if (st.session_state.auto_close or remaining <= 0) and (not submit_btn) else "NO"

        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        user_agent = st.context.headers.get("user-agent", "") if hasattr(st, "context") else ""

        row = [
            ts,
            SESSION,
            st.session_state.nom,
            st.session_state.matricule,
            st.session_state.etablissement,
            str(score_raw),
            str(score_sur20),
            str(st.session_state.tab_switch_count),
            was_auto_closed,
            user_agent,
        ] + [(answer_map[f"Q{i}"] or "Sans réponse") for i in range(1, 31)]

        ws = get_ws()
        if sheet_has_attempt(ws, SESSION, st.session_state.matricule):
            st.error("Tentative déjà enregistrée (double soumission détectée).")
            st.session_state.submitted = True
            st.rerun()

        append_attempt(ws, row)

        st.session_state.submitted = True

        if was_auto_closed == "YES":
            st.error("🛑 Soumission automatique (sortie de page / temps écoulé).")
        st.success(f"✅ Soumis. Note: {score_sur20}/20  ({score_raw}/30)")
        st.stop()

    time.sleep(1)
    st.rerun()

# ============================================================
# ADMIN
# ============================================================
st.markdown("---")
with st.expander("🔐 Espace Administrateur"):
    code = st.text_input("Code admin", type="password")
    if code == CODE_ADMIN:
        ws = get_ws()
        values = ws.get_all_values()
        if len(values) <= 1:
            st.warning("Aucun résultat pour le moment.")
        else:
            df = pd.DataFrame(values[1:], columns=values[0])
            df_sess = df[df["session"] == SESSION].copy()
            df_sess["score_sur20"] = pd.to_numeric(df_sess["score_sur20"], errors="coerce")

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Total", len(df_sess))
            with c2:
                st.metric("Moyenne", f"{df_sess['score_sur20'].mean():.2f}/20")
            with c3:
                st.metric("Max", f"{df_sess['score_sur20'].max():.2f}/20")
            with c4:
                st.metric("Auto-closings", int((df_sess["was_auto_closed"] == "YES").sum()))

            st.dataframe(
                df_sess[["timestamp","nom","matricule","score_raw","score_sur20","tab_switch_count","was_auto_closed"]],
                use_container_width=True
            )

            st.download_button(
                "📥 Télécharger CSV (session)",
                data=df_sess.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"RESULTATS_{SESSION}.csv",
                mime="text/csv",
                use_container_width=True
            )
    elif code != "":
        st.error("Code incorrect.")
