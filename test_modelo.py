import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from modelo import Paciente, calcular_metas, gerar_plano, meta_calorica, tmb_mifflin


def paciente(**kw):
    base = dict(sexo="F", idade=55, peso_kg=82, altura_cm=160,
                atividade="leve", objetivo="emagrecer")
    base.update(kw)
    return Paciente(**base)


def test_tmb_mifflin_mulher():
    # 10*82 + 6.25*160 - 5*55 - 161 = 1384
    assert tmb_mifflin(paciente()) == pytest.approx(1384)


def test_deficit_aplicado_com_sobrepeso():
    manter = meta_calorica(paciente(objetivo="manter"))
    emagrecer = meta_calorica(paciente(objetivo="emagrecer"))
    assert manter - emagrecer == pytest.approx(500)


def test_piso_calorico():
    assert meta_calorica(paciente(peso_kg=45, altura_cm=170, idade=80,
                                  objetivo="manter")) >= 1200


def test_percentuais_invalidos():
    with pytest.raises(ValueError):
        calcular_metas(2000, 0.5, 0.3, 0.3)


def test_plano_respeita_meta_de_carboidratos():
    plano = gerar_plano(paciente())
    alvo = plano["metas"].carb_g
    assert plano["totais"]["carb"] == pytest.approx(alvo, rel=0.05)


def test_plano_tem_5_refeicoes_e_fibras_suficientes():
    plano = gerar_plano(paciente())
    assert len(plano["refeicoes"]) == 5
    assert plano["totais"]["fibra"] >= plano["metas"].fibra_g
