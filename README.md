# 🥗 Dieta DM2 — Planejamento alimentar para Diabetes tipo 2

Modelo computacional em Python com interface web em Streamlit que calcula metas
calóricas e de macronutrientes e monta um cardápio diário em gramas, controlando
a distribuição de carboidratos e a carga glicêmica.

> ⚠️ **Aviso:** projeto educacional. Não substitui nutricionista ou endocrinologista.
> Não considera medicamentos (insulina, sulfonilureias), doença renal, alergias
> ou risco de hipoglicemia.

## Como o modelo funciona

1. **TMB** pela equação de Mifflin-St Jeor × fator de atividade.
2. **Meta calórica**: déficit configurável (padrão 500 kcal) se objetivo = emagrecer e IMC ≥ 25, com piso de segurança.
3. **Macros** (padrão 45% carb / 20% prot / 35% gord) e fibras ≥ 14 g/1000 kcal.
4. **Distribuição dos carboidratos** em 5 refeições (20/10/30/10/30%).
5. **Cardápio** em gramas a partir de um banco de alimentos, com **carga glicêmica** (IG × carb ÷ 100) por refeição e no dia.

## Rodando localmente

```bash
git clone https://github.com/SEU-USUARIO/dieta-dm2.git
cd dieta-dm2
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Sem interface (terminal): `python modelo.py`

## Testes

```bash
pip install -r requirements-dev.txt
pytest
```

## Deploy no Streamlit Community Cloud

1. Suba o repositório para o GitHub (público ou privado).
2. Acesse [share.streamlit.io](https://share.streamlit.io) e entre com o GitHub.
3. **New app** → escolha o repositório, branch `main` e arquivo principal `app.py`.
4. **Deploy**.

## Estrutura

```
├── app.py               # interface Streamlit
├── modelo.py            # lógica do modelo (sem dependência de UI)
├── tests/test_modelo.py
├── requirements.txt
└── .github/workflows/ci.yml
```

## Personalização

- **Alimentos**: edite a lista `BANCO` em `modelo.py` (valores por 100 g).
- **Refeições**: edite `TEMPLATE` (percentual de carboidratos e papel de cada alimento).
- **Próximos passos**: otimização linear (`scipy.optimize.linprog`), tabela TACO completa em CSV, restrições de sódio e gordura saturada.

## Licença

MIT
