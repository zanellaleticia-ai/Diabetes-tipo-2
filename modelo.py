"""
Modelo computacional de planejamento alimentar para Diabetes Mellitus tipo 2.

ATENÇÃO: ferramenta educacional. Não substitui nutricionista/endocrinologista.
Valores nutricionais aproximados (por 100 g, base em tabelas tipo TACO).

Etapas:
  1. Gasto energético: TMB (Mifflin-St Jeor) x fator de atividade
  2. Meta calórica ajustada ao objetivo
  3. Macronutrientes (faixas típicas de diretrizes SBD/ADA)
  4. Distribuição de carboidratos entre as refeições
  5. Montagem do cardápio em gramas + verificações (fibras, carga glicêmica)
"""
from __future__ import annotations

from dataclasses import dataclass

FATORES_ATIVIDADE = {
    "sedentario": 1.2,
    "leve": 1.375,
    "moderado": 1.55,
    "intenso": 1.725,
}


# ----------------------------------------------------------------------------
# Paciente e metas
# ----------------------------------------------------------------------------
@dataclass
class Paciente:
    sexo: str                     # "M" ou "F"
    idade: int
    peso_kg: float
    altura_cm: float
    atividade: str = "leve"       # chave de FATORES_ATIVIDADE
    objetivo: str = "emagrecer"   # "emagrecer" | "manter"

    @property
    def imc(self) -> float:
        return self.peso_kg / (self.altura_cm / 100) ** 2


@dataclass
class Metas:
    kcal: float
    carb_g: float
    prot_g: float
    gord_g: float
    fibra_g: float


def tmb_mifflin(p: Paciente) -> float:
    base = 10 * p.peso_kg + 6.25 * p.altura_cm - 5 * p.idade
    return base + (5 if p.sexo.upper() == "M" else -161)


def meta_calorica(p: Paciente, deficit: float = 500) -> float:
    get = tmb_mifflin(p) * FATORES_ATIVIDADE[p.atividade]
    if p.objetivo == "emagrecer" and p.imc >= 25:
        get -= deficit
    piso = 1200 if p.sexo.upper() == "F" else 1500
    return max(get, piso)


def calcular_metas(kcal: float, pct_carb: float = 0.45,
                   pct_prot: float = 0.20, pct_gord: float = 0.35) -> Metas:
    if abs(pct_carb + pct_prot + pct_gord - 1) > 1e-6:
        raise ValueError("Os percentuais de macronutrientes devem somar 100%.")
    return Metas(
        kcal=kcal,
        carb_g=kcal * pct_carb / 4,
        prot_g=kcal * pct_prot / 4,
        gord_g=kcal * pct_gord / 9,
        fibra_g=14 * kcal / 1000,  # mínimo: 14 g por 1000 kcal
    )


# ----------------------------------------------------------------------------
# Banco de alimentos
# ----------------------------------------------------------------------------
@dataclass(frozen=True)
class Alimento:
    nome: str
    carb: float
    prot: float
    gord: float
    fibra: float
    ig: int = 0  # índice glicêmico

    @property
    def kcal(self) -> float:
        return 4 * self.carb + 4 * self.prot + 9 * self.gord


BANCO: dict[str, Alimento] = {a.nome: a for a in [
    Alimento("Pão integral", 49.9, 9.4, 3.7, 6.9, 51),
    Alimento("Aveia em flocos", 66.6, 13.9, 8.5, 9.1, 55),
    Alimento("Arroz integral cozido", 25.8, 2.6, 1.0, 2.7, 50),
    Alimento("Feijão cozido", 13.6, 4.8, 0.5, 8.5, 30),
    Alimento("Batata-doce cozida", 18.4, 0.6, 0.1, 2.2, 63),
    Alimento("Maçã", 15.2, 0.3, 0.0, 1.3, 36),
    Alimento("Iogurte natural", 5.0, 4.0, 3.0, 0.0, 35),
    Alimento("Ovo cozido", 0.6, 13.3, 9.5, 0.0, 0),
    Alimento("Peito de frango grelhado", 0.0, 32.0, 2.5, 0.0, 0),
    Alimento("Tilápia grelhada", 0.0, 26.0, 2.7, 0.0, 0),
    Alimento("Brócolis cozido", 4.4, 2.1, 0.6, 3.4, 15),
    Alimento("Salada de folhas", 2.0, 1.3, 0.2, 1.5, 15),
    Alimento("Castanha-do-pará", 12.3, 14.5, 63.5, 7.9, 10),
    Alimento("Azeite de oliva", 0.0, 0.0, 100.0, 0.0, 0),
]}

# Papéis: "carb" (ajustado p/ bater meta), "prot", "gord", "fixo" (gramas fixas)
TEMPLATE: dict[str, dict] = {
    "Café da manhã": {"pct_carb": 0.20, "itens": [
        ("Pão integral", "carb"), ("Maçã", "carb"), ("Ovo cozido", "prot")]},
    "Lanche da manhã": {"pct_carb": 0.10, "itens": [
        ("Iogurte natural", "carb"), ("Castanha-do-pará", "fixo", 15)]},
    "Almoço": {"pct_carb": 0.30, "itens": [
        ("Arroz integral cozido", "carb"), ("Feijão cozido", "carb"),
        ("Peito de frango grelhado", "prot"), ("Salada de folhas", "fixo", 100),
        ("Brócolis cozido", "fixo", 100), ("Azeite de oliva", "gord")]},
    "Lanche da tarde": {"pct_carb": 0.10, "itens": [
        ("Maçã", "carb"), ("Castanha-do-pará", "fixo", 15)]},
    "Jantar": {"pct_carb": 0.30, "itens": [
        ("Batata-doce cozida", "carb"), ("Tilápia grelhada", "prot"),
        ("Brócolis cozido", "fixo", 100), ("Salada de folhas", "fixo", 100),
        ("Azeite de oliva", "gord")]},
}


# ----------------------------------------------------------------------------
# Cálculo de porções
# ----------------------------------------------------------------------------
def _nutrientes(nome: str, gramas: float) -> dict:
    a, f = BANCO[nome], gramas / 100
    return {
        "alimento": nome,
        "gramas": round(gramas),
        "kcal": a.kcal * f,
        "carb": a.carb * f,
        "prot": a.prot * f,
        "gord": a.gord * f,
        "fibra": a.fibra * f,
        "cg": a.ig * a.carb * f / 100,  # carga glicêmica
    }


def _soma(linhas: list[dict]) -> dict:
    chaves = ("kcal", "carb", "prot", "gord", "fibra", "cg")
    return {k: sum(l[k] for l in linhas) for k in chaves}


def montar_refeicao(cfg: dict, metas: Metas) -> list[dict]:
    frac = cfg["pct_carb"]
    carb_alvo, prot_alvo, gord_alvo = (metas.carb_g * frac,
                                       metas.prot_g * frac,
                                       metas.gord_g * frac)
    itens = cfg["itens"]
    fixos = [i for i in itens if i[1] == "fixo"]
    carbs = [i for i in itens if i[1] == "carb"]
    protes = [i for i in itens if i[1] == "prot"]
    gords = [i for i in itens if i[1] == "gord"]

    porcoes: list[tuple[str, float]] = [(i[0], i[2]) for i in fixos]

    def atual() -> dict:
        return _soma([_nutrientes(n, g) for n, g in porcoes])

    if carbs:
        orc = max(carb_alvo - atual()["carb"], 0) / len(carbs)
        porcoes += [(n, orc / BANCO[n].carb * 100) for n, _ in carbs]

    if protes:
        falta = max(prot_alvo - atual()["prot"], 0) / len(protes)
        for n, _ in protes:
            g = falta / BANCO[n].prot * 100
            porcoes.append((n, min(max(g, 50), 200)))

    for n, _ in gords:
        falta = max(gord_alvo - atual()["gord"], 0)
        porcoes.append((n, min(falta, 15)))

    return [_nutrientes(n, g) for n, g in porcoes if g >= 1]


def gerar_plano(p: Paciente, pct_carb: float = 0.45, pct_prot: float = 0.20,
                pct_gord: float = 0.35, deficit: float = 500) -> dict:
    kcal = meta_calorica(p, deficit)
    metas = calcular_metas(kcal, pct_carb, pct_prot, pct_gord)

    refeicoes = []
    for nome, cfg in TEMPLATE.items():
        linhas = montar_refeicao(cfg, metas)
        refeicoes.append({"nome": nome, "itens": linhas, "totais": _soma(linhas)})

    total = _soma([l for r in refeicoes for l in r["itens"]])

    avisos = []
    if total["fibra"] < metas.fibra_g:
        avisos.append("Fibras abaixo da meta: inclua mais leguminosas e hortaliças.")
    if abs(total["kcal"] - kcal) / kcal > 0.15:
        avisos.append("O cardápio diverge mais de 15% da meta calórica; "
                      "ajuste porções ou o template.")
    if p.imc < 18.5:
        avisos.append("IMC abaixo de 18,5: procure acompanhamento profissional.")

    return {
        "paciente": p,
        "tmb": tmb_mifflin(p),
        "metas": metas,
        "refeicoes": refeicoes,
        "totais": total,
        "avisos": avisos,
    }


if __name__ == "__main__":
    plano = gerar_plano(Paciente("F", 55, 82, 160, "leve", "emagrecer"))
    m, t = plano["metas"], plano["totais"]
    print(f"Meta: {m.kcal:.0f} kcal | Plano: {t['kcal']:.0f} kcal | "
          f"Carb {t['carb']:.0f} g | Fibra {t['fibra']:.0f} g | CG {t['cg']:.0f}")
    for r in plano["refeicoes"]:
        print(f"\n{r['nome']} ({r['totais']['kcal']:.0f} kcal)")
        for i in r["itens"]:
            print(f"  - {i['alimento']}: {i['gramas']} g")
