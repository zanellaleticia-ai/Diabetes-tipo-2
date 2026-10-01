"""Interface Streamlit do modelo de dieta para Diabetes tipo 2."""
import pandas as pd
import streamlit as st

from modelo import FATORES_ATIVIDADE, Paciente, gerar_plano

st.set_page_config(page_title="Dieta DM2", page_icon="🥗", layout="wide")

st.title("🥗 Planejamento alimentar — Diabetes tipo 2")
st.warning(
    "Ferramenta **educacional**. Não substitui a orientação de nutricionista "
    "ou endocrinologista. Não considera medicamentos, doença renal, alergias "
    "ou risco de hipoglicemia."
)

# ----------------------------- Entradas ------------------------------------
with st.sidebar:
    st.header("Dados do paciente")
    sexo = st.radio("Sexo", ["F", "M"], horizontal=True)
    idade = st.number_input("Idade (anos)", 18, 100, 55)
    peso = st.number_input("Peso (kg)", 30.0, 250.0, 82.0, step=0.5)
    altura = st.number_input("Altura (cm)", 120.0, 230.0, 160.0, step=0.5)
    atividade = st.selectbox("Nível de atividade", list(FATORES_ATIVIDADE), index=1)
    objetivo = st.selectbox("Objetivo", ["emagrecer", "manter"])

    st.header("Macronutrientes (%)")
    pct_carb = st.slider("Carboidratos", 30, 60, 45)
    pct_prot = st.slider("Proteínas", 15, 35, 20)
    pct_gord = 100 - pct_carb - pct_prot
    st.metric("Gorduras (restante)", f"{pct_gord}%")
    deficit = st.slider("Déficit calórico (kcal)", 0, 700, 500, step=50,
                        disabled=(objetivo == "manter"))

if not 20 <= pct_gord <= 40:
    st.error("Ajuste os percentuais: gorduras devem ficar entre 20% e 40%.")
    st.stop()

paciente = Paciente(sexo, int(idade), peso, altura, atividade, objetivo)
plano = gerar_plano(paciente, pct_carb / 100, pct_prot / 100, pct_gord / 100, deficit)
metas, totais = plano["metas"], plano["totais"]

# ----------------------------- Resumo --------------------------------------
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("IMC", f"{paciente.imc:.1f}")
c2.metric("TMB", f"{plano['tmb']:.0f} kcal")
c3.metric("Meta diária", f"{metas.kcal:.0f} kcal")
c4.metric("Plano gerado", f"{totais['kcal']:.0f} kcal",
          f"{totais['kcal'] - metas.kcal:+.0f} vs meta", delta_color="off")
c5.metric("Carga glicêmica", f"{totais['cg']:.0f}")

for aviso in plano["avisos"]:
    st.info(aviso)

# ----------------------------- Cardápio ------------------------------------
aba_cardapio, aba_macros = st.tabs(["Cardápio", "Metas vs plano"])

with aba_cardapio:
    for refeicao in plano["refeicoes"]:
        t = refeicao["totais"]
        with st.expander(
            f"{refeicao['nome']} — {t['kcal']:.0f} kcal | "
            f"carb {t['carb']:.0f} g | CG {t['cg']:.0f}",
            expanded=True,
        ):
            df = pd.DataFrame(refeicao["itens"]).rename(columns={
                "alimento": "Alimento", "gramas": "Gramas", "kcal": "kcal",
                "carb": "Carb (g)", "prot": "Prot (g)", "gord": "Gord (g)",
                "fibra": "Fibra (g)", "cg": "CG"})
            st.dataframe(df.round(1), hide_index=True, use_container_width=True)

    todas = pd.DataFrame(
        [{"Refeição": r["nome"], "Carboidratos (g)": r["totais"]["carb"]}
         for r in plano["refeicoes"]]
    ).set_index("Refeição")
    st.subheader("Distribuição de carboidratos ao longo do dia")
    st.bar_chart(todas)

with aba_macros:
    comp = pd.DataFrame({
        "Meta": [metas.carb_g, metas.prot_g, metas.gord_g, metas.fibra_g],
        "Plano": [totais["carb"], totais["prot"], totais["gord"], totais["fibra"]],
    }, index=["Carboidratos (g)", "Proteínas (g)", "Gorduras (g)", "Fibras (g, mín.)"])
    st.dataframe(comp.round(0), use_container_width=True)
    st.bar_chart(comp)

    csv = pd.DataFrame(
        [{"Refeição": r["nome"], **i} for r in plano["refeicoes"] for i in r["itens"]]
    ).to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Baixar cardápio (CSV)", csv, "cardapio_dm2.csv", "text/csv")
