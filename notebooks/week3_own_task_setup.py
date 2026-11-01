"""Подготовка своей задачи раздела 12. Запросов к модели здесь нет."""

import csv
from decimal import Decimal, InvalidOperation
from io import StringIO
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
BASE_ENV = {
    "measurements.csv": (PROJECT / "data/measurements.csv").read_text(encoding="utf-8"),
    "protocol.md": (
        "Учебный расчёт pV. volume_l задан в литрах, pressure_kpa — в кПа.\n"
        "pV = volume_l * pressure_kpa, единица результата — кПа·л.\n"
        "Исключить только строку №7; строки данных нумеруются с 1 без заголовка.\n"
        "Это заранее принятое правило данного опыта. Причину отклонения не устанавливать.\n"
        "Входные файлы сохранять без изменений.\n"
    ),
}
MY_ENV = BASE_ENV.copy()
MY_TASK = (
    "Прочитай measurements.csv и protocol.md. Вычисли pV для каждой строки данных. "
    "Исключи строку №7 по protocol.md и найди среднее арифметическое pV остальных строк. "
    "Для арифметики используй calc. В result.txt запиши только одно число: "
    "среднее в кПа·л, с точностью не хуже 0.001. Входные файлы не изменяй."
)

# Эталон вычисляет проверяющая программа; в запрос модели он не включён.
reference_rows = list(csv.DictReader(StringIO(BASE_ENV["measurements.csv"])))
reference_products = [
    Decimal(row["volume_l"]) * Decimal(row["pressure_kpa"])
    for number, row in enumerate(reference_rows, start=1)
    if number != 7
]
REFERENCE = sum(reference_products, Decimal(0)) / Decimal(len(reference_products))


def my_phi(env):
    """Принимает конечное число в допуске 0.001 и неизменные входы."""
    try:
        actual = Decimal(env.get("result.txt", "").strip())
        return (
            actual.is_finite()
            and abs(actual - REFERENCE) < Decimal("0.001")
            and all(env.get(name) == text for name, text in BASE_ENV.items())
        )
    except (InvalidOperation, TypeError, ValueError, AttributeError):
        return False


# Проверяем критерий на независимых примерах до первого запуска агента.
correct = {**BASE_ENV, "result.txt": str(REFERENCE)}
wrong = {**BASE_ENV, "result.txt": str(REFERENCE + Decimal(1))}
changed_input = {**correct, "measurements.csv": BASE_ENV["measurements.csv"] + "\n"}
fixtures = {
    "верное число": (correct, True),
    "ошибка на 1": (wrong, False),
    "результат отсутствует": (BASE_ENV.copy(), False),
    "изменён вход": (changed_input, False),
    "NaN": ({**BASE_ENV, "result.txt": "NaN"}, False),
}
for label, (fixture, expected) in fixtures.items():
    observed = my_phi(fixture)
    assert observed == expected, f"Критерий неверно обработал пример: {label}"
    print(f"Проверка критерия: {label} -> {int(observed)}")

print("Исходных строк:", len(reference_rows), "| после исключения:", len(reference_products))
print("Эталон проверяющей программы:", REFERENCE)
print("Среда и критерий готовы. Агент ещё не запускался.")
