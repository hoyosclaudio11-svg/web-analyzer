from practice_coverage import build_practice_coverage


def test_twenty_practices_separate_measured_signals_from_unknowns():
    items = build_practice_coverage(
        {"total": 2},
        {"bloqueantes": 1, "con_async_defer": 1},
        {
            "auditorias": [
                {"id": "modern-image-formats", "estado": "issue"},
                {"id": "unminified-css", "estado": "pass"},
            ]
        },
        {"Content-Encoding": "br", "Cache-Control": "public, max-age=300", "CF-Ray": "abc"},
    )

    assert len(items) == 20
    assert items[0]["estado"] == "medido_con_hallazgos"
    assert items[3]["estado"] == "indicio"
    assert items[5]["estado"] == "requiere_servidor"
    assert items[10]["estado"] == "medido_con_hallazgos"
    assert items[12]["estado"] == "medido"
    assert items[19]["estado"] == "proceso_interno"


def test_missing_lighthouse_results_are_not_reported_as_a_pass():
    items = build_practice_coverage({}, {}, None, {})

    assert items[0]["estado"] == "sin_evidencia"
    assert items[4]["estado"] == "sin_evidencia"
    assert items[18]["estado"] == "sin_evidencia"
