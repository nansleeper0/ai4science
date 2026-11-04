---
type: ЗапросКГрафу
source: Wikidata
retrieved: 2026-11-04
---
# Запрос 2026-11-04 Wikidata X-ray pulsar

Инструмент и аргументы: wikidata_search (query "X-ray pulsar", language en) → Q2979836; wikidata_sparql SELECT по Q2979836 со свойством P31 (instance of).

Текст успешного SELECT:
```
SELECT ?item ?itemLabel ?instance ?instanceLabel WHERE {
  wd:Q2979836 rdfs:label ?itemLabel .
  wd:Q2979836 wdt:P31 ?instance .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
```

Найдено: 29 строк; отобрано в проект: 1 — Q2979836 (X-ray pulsar, "pulsar which emits X-rays") со свойством P31 = Q17444909 (astronomical object type). Сведения внесены в заметку Анализ сравнения моделей.

## Связи
- тип: [[ЗапросКГрафу]]
- решает: [[подзадача-wikidata]]