# ДЗ2 AI4Science: форма импульса EXO2030+375 и яркость

Пакет вычислительной проверки: десять наблюдений, 34 периода × 100 фазовых бинов в каждом. Сравнивается показатель R — отношение интегралов среднего профиля в двух заранее выбранных фазовых окнах.

**Результат:** E=0,572719; 95% блочный bootstrap-интервал [0,534133; 0,612781]. Яркость измерена средним темпом счёта; физическая светимость не вычислялась.

- [Отчёт](reports/hw2.md) — пока черновик на чтении у автора работы.
- [Методика до запусков](METHOD.md).
- [Данные и их происхождение](data/profile_luminosity_10bins/README.md).
- [Профили](results/hw2/figures/profiles.png) и [R от яркости](results/hw2/figures/shape_vs_brightness.png).

## Проверка и повторение расчётов

Python 3.10.12; версии библиотек закреплены в requirements-hw2.txt.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-hw2.txt
.venv/bin/python -m pytest checks/hw2 -q
.venv/bin/python src/profile_synthetic.py --output-dir results/hw2/reproduced_synthetic
.venv/bin/python src/profile_real.py --out results/hw2/reproduced_real
.venv/bin/python src/plot_profile_results.py
```

Ожидается 41 пройденный тест. Расчёты в отдельные каталоги позволяют сверить результаты, сохраняя исходные файлы. Скрипт рисунков читает сохранённый real_corrected/.

## Карта артефактов

| Путь | Назначение |
|---|---|
| `checks/hw2/` | 18 тестов ядра/входов, 7 синтетики, 16 реального расчёта |
| `src/profile_shape.py` | Загрузчик и метрики |
| `src/profile_synthetic.py` | Парный контроль на 30 общих seed |
| `src/profile_real.py` | Реальные профили и 2000 bootstrap-повторов |
| `results/hw2/synthetic_corrected/` | Актуальный синтетический результат |
| `results/hw2/real_corrected/` | Актуальный реальный результат |
| `results/hw2/synthetic_failed_attempt/` | Сохранённый неудачный синтетический запуск |
| `results/hw2/real/` | Сохранённый запуск bootstrap с ошибочными общими индексами |
| `results/hw2/caught_error_*` | Доказательство обнаружения ранней ошибки загрузчика |
| `results/hw2/environment.json` | Фактически проверенное окружение |

Старая версия загрузчика доступна в ветке `hw2-bug-missing-sha`: один и тот же тест `test_manifest_sha_rejects_tampered` на ней падает, на исправленной версии проходит. Восстановление ранней версии описано в caught_error_provenance.json.

Методика зафиксирована коммитом `39c32c1` до прогонов. Метка `hw2` и публикация пакета пока не выполнены. Личные планы и исходная история рабочих проектов в пакет не входят.

Происхождение кода и текста, работа учебного агента AI4Science/Goose и помощь Codex указаны в разделе 9 отчёта.
