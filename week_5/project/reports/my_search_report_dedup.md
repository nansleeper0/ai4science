---
type: Отчёт
---
# Поиск по исправленной библиотеке: X-ray pulsar variability

## Связи
- тип: [[Отчёт]]
- выполняет: [[исправление-библиотеки-неделя5]]
- ссылаетсяНа: [[Источник Bult 2015]]
- ссылаетсяНа: [[Источник LS1997]]
- ссылаетсяНа: [[Источник M2024]]

[источник] OpenAlex, запрос: https://api.openalex.org/works?search=X-ray+pulsar+variability&per_page=100&filter=has_abstract%3Atrue&select=id%2Cdoi%2Cdisplay_name%2Cpublication_year%2Ccited_by_count%2Cabstract_inverted_index, дата: 2026-11-05, работ: 20 (18 исходных + 2 добавленные)

[порождено] Корпус исправлен по сохранённому library/search_response_full.json: 18 исходных записей сохранены, последними добавлены две работы с числом элементов abstract_inverted_index больше 40:
- W2188719749 «Determination of parameters of Long-Term variability of the X-ray pulsar LMC X-4» (129 элементов)
- W2594250205 «The Stochastic X-Ray Variability of the Accreting Millisecond Pulsar MAXI J0911–655» (99 элементов)

[порождено] W2133381428 исключён из исправленного корпуса: у него 26 элементов abstract_inverted_index, а исходный notebook отбирал только записи с числом элементов больше 40.

## coupling between periodic and aperiodic variability in X-ray pulsars

| место | BM25 | вектор |
|---|---|---|
| 1 | On the Relationship between the Periodic and Aperiodic Variability of Accreting X‐Ray Pulsars (W2016427691) | On the Relationship between the Periodic and Aperiodic Variability of Accreting X‐Ray Pulsars (W2016427691) |
| 2 | Connecting the coherent and stochastic X-ray variability of accreting millisecond pulsars (W2274579547) | A turbulent model of time variability in X-ray binary pulsars (W2000089589) |
| 3 | THE APERIODIC X-RAY VARIABILITY OF THE ACCRETING MILLISECOND PULSAR SAX J1808.4−3658 (W253850377) | Photometric Variability of Be/X-Ray Pulsar Binaries in the Small Magellanic Cloud (W1984285302) |

[порождено] Обе модели ставят первой статью Lazzati & Stella (W2016427691). Векторный поиск не изменился; BM25 сохранил те же три работы.

[написано] Для вопроса о связи пульсаций и шумовой переменности оба способа находят статью Lazzati и Stella первой.

## broad wings around pulse frequency peaks in power spectra

| место | BM25 | вектор |
|---|---|---|
| 1 | On the Relationship between the Periodic and Aperiodic Variability of Accreting X‐Ray Pulsars (W2016427691) | On the Relationship between the Periodic and Aperiodic Variability of Accreting X‐Ray Pulsars (W2016427691) |
| 2 | The X-ray pulsar A0535 + 26 - Pulse profile and its time variability in hard X-rays (W2044775182) | A turbulent model of time variability in X-ray binary pulsars (W2000089589) |
| 3 | A turbulent model of time variability in X-ray binary pulsars (W2000089589) | The Stochastic X-Ray Variability of the Accreting Millisecond Pulsar MAXI J0911–655 (W2594250205) |

[порождено] Первой в обеих моделях — Lazzati & Stella (W2016427691). Векторный поиск теперь выводит на третье место добавленную работу MAXI J0911–655 (W2594250205).

[написано] Для вопроса о широких крыльях оба способа находят статью Lazzati и Stella первой. Остальная выдача различается.

## accretion column eclipse phase resolved variability

| место | BM25 | вектор |
|---|---|---|
| 1 | Post-glitch variability in the anomalous X-ray pulsar 1RXS J170849.0–400910 (W2150552231) | The Stochastic X-Ray Variability of the Accreting Millisecond Pulsar MAXI J0911–655 (W2594250205) |
| 2 | On the Relationship between the Periodic and Aperiodic Variability of Accreting X‐Ray Pulsars (W2016427691) | Determination of parameters of Long-Term variability of the X-ray pulsar LMC X-4 (W2188719749) |
| 3 | X-ray variability of the pulsar Vela X-1 as observed with ART-P/Granat (W2084034713) | The Detection of Variability from the Candidate Infrared Counterpart to the Anomalous X-Ray Pulsar 1E 1048.1−5937 (W2038558267) |

[порождено] Векторный поиск выводит на первые места две добавленные работы (MAXI J0911–655 и LMC X-4). По названиям и аннотациям о затмении аккреционной колонны по-прежнему нет.

[написано] По затмению аккреционной колонны прямого ответа не получилось.

## Почему шумовая переменность зависит от фазы пульсаций?

| место | BM25 | вектор |
|---|---|---|
| 1 | — (нет положительных оценок) | The Stochastic X-Ray Variability of the Accreting Millisecond Pulsar MAXI J0911–655 (W2594250205) |
| 2 | — | A turbulent model of time variability in X-ray binary pulsars (W2000089589) |
| 3 | — | Post-glitch variability in the anomalous X-ray pulsar 1RXS J170849.0–400910 (W2150552231) |

[порождено] BM25 не дал положительных оценок для русского запроса: кириллица токенизируется (она есть в регулярном выражении), но BM25 не находит лексических совпадений русских слов с англоязычным корпусом. Векторный поиск без отсечения по знаку вернул три работы; добавленная MAXI J0911–655 — первая.

[написано] На русском смысловой поиск находит близкие работы, а поиск по словам не даёт результатов.

## Какие ограничения есть у моделей переменности EXO 2030+375?

| место | BM25 | вектор |
|---|---|---|
| 1 | — (нет положительных оценок) | The Detection of Variability from the Candidate Infrared Counterpart to the Anomalous X-Ray Pulsar 1E 1048.1−5937 (W2038558267) |
| 2 | — | Determination of parameters of Long-Term variability of the X-ray pulsar LMC X-4 (W2188719749) |
| 3 | — | The Stochastic X-Ray Variability of the Accreting Millisecond Pulsar MAXI J0911–655 (W2594250205) |

[порождено] BM25 снова без положительных оценок для русского запроса (кириллица токенизируется, но лексических совпадений с англоязычным корпусом нет). Векторный поиск вернул три работы, среди них добавленные LMC X-4 и MAXI J0911–655; прямого ответа об ограничениях моделей EXO 2030+375 нет.

[написано] Для вопроса об EXO2030+375 нужна более точная подборка литературы.

## Сравнение с первоначальными результатами

[порождено] Для англоязычных запросов выдачи в основном совпали с первоначальным отчётом; главное отличие — добавленные работы W2188719749 (LMC X-4) и W2594250205 (MAXI J0911–655) вышли на первые места векторного поиска по запросу про аккреционную колонну и по русскоязычным запросам. Для русскоязычных запросов BM25 не даёт положительных оценок: кириллица токенизируется (она есть в регулярном выражении), но BM25 не находит лексических совпадений русских слов с англоязычным корпусом; векторный поиск работает без отсечения по знаку.

## Мой итог и приёмка

[написано] На пятой неделе я сравнил поиск по словам и по смыслу на пяти запросах по переменности рентгеновских пульсаров. В первоначальной библиотеке обнаружились дубли. После исправления в ней осталось 20 разных работ.

[написано] Учебный агент исправил корпус и отчёт, первоначальные результаты сохранены. Итоговая проверка прошла: 43 объекта, 74 связи, код 0. Результат недели принимаю как основу для дальнейшей работы над обзором.
