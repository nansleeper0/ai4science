"""Записать подтверждение двух ответов после самостоятельного чтения страниц3/5."""

import argparse
import json
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--checked',action='store_true',help='Пользователь прочитал указанные места PDF и подтвердил значения')
args=parser.parse_args()
if not args.checked:
    parser.error('Сначала прочитайте страницы3/5; --checked означает ваше фактическое подтверждение')

root=Path(__file__).resolve().parent
path=root/'results/week3_answers_review.md'
lines=path.read_text(encoding='utf-8').splitlines()
outcomes={
    2:'подтверждено пользователем: источник, прибор, диапазон кривых блеска и расстояние совпадают',
    3:'исправлено: обоснование P>0.1с находится на PDF-странице3, не2; на странице5 также есть типичные P>1с',
}
updated=set()
for i,line in enumerate(lines):
    for number,label in [(2,'5'),(3,'3, 5')]:
        if line.startswith(f'| {number} | {label} |'):
            cells=[s.strip() for s in line.strip('|').split('|')]
            if len(cells)!=4 or not cells[2]:
                raise ValueError(f'Не подготовлена цитата ответа{number}')
            cells[3]=outcomes[number]
            lines[i]='| '+' | '.join(cells)+' |'
            updated.add(number)
if updated!={2,3}:
    raise ValueError('Не найдены обе строки ответов; файл сохранён')
path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
receipt=root/'results/week3_finish_prepared.json'
data=json.loads(receipt.read_text());data['human_review']='article completed by explicit user command after reading pages 3 and 5'
receipt.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(root/'STATUS.md').write_text('''# STATUS.md — текущее состояние

## Где мы
Notebook и собственная задача приняты. L1–L3 готовы. Пользователь подтвердил три тезиса по PDF; три исходных ответа сверены, ссылка в третьем уточнена. Инструкции, указатель и документация подготовлены.

## Дальше
Сохранить методику и контекст в git до двух сравнительных запусков, подготовить копии, выполнить A/B и навигацию. Затем заполнить протоколы по фактическим ответам, дополнить дневник и пройти итоговую проверку.

## Действует
Данные и checks только для чтения, причина отклонения №7 не установлена. Результаты V0332+53 не переносить автоматически на EXO2030+375. Git и публикацию выполняет пользователь.
''',encoding='utf-8')
(root/'results/week3_review_progress.md').write_text('''# Текущее состояние недели3

Пользователь подтвердил тезисы5/7/10 в чате; первый исходный ответ покрыт той же проверкой параметров, что тезис5. Два оставшихся ответа подтверждены явным запуском команды --checked после чтения PDF-страниц3/5. Таблицы заполнены по фактически заявленным проверкам.

Следующий этап: два A/B-запуска и одна навигационная сессия. Их результаты ещё не получены. Протоколы и итоговый отчёт заполняются наставником после получения фактических ответов.
''',encoding='utf-8')
print('Подтверждение чтения записано. Три тезиса L2 и три исходных ответа сверены.')
print('Следующая проверка: python3 verify_week3_local.py --section article --no-git')
