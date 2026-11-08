# Прогон v3: 01 и 03 — что пришло на вход и что получилось

Дата: 2026-11-08. Версия скилла: без hooks_library, с проверкой связки (FLOW), лимит новой съёмки 25%.

**Как шёл прогон.**
1. Свежий агент-автор получил только SKILL.md, папку reference/ и сообщение дизайнера.
2. Он сам разобрал сценарий, набросал идеи, написал 20 вариантов и прогнал их через правила check.py.
3. Связку каждого варианта проверял отдельный агент-ревьюер. Он видел только `flow.md` и `flow_review.md` и не знал, как и зачем писались хуки.
4. Вердикты ревьюера (`flow.json`) check.py превратил в отказы `FLOW`. Автор переписал отклонённые варианты (не больше 2 раундов), и каждую замену снова проверял новый ревьюер.

Таблица разбора сценария в eval считалась подтверждённой без дизайнера. В реальной работе её подтверждает дизайнер.

| | 01 B03 Morning rush | 03 SL_B05_skeptic |
|---|---|---|
| Форма входа | таймкоды, VO + текст + визуал | только VO, без таймкодов, текста и визуала |
| Область | только хук | только хук |
| Сгенерировано | 20 | 20 (+2 замены) |
| Прошли правила с 1-го раза | 20 / 20 | 20 / 20 |
| Связка (FLOW) в 1-м раунде | 20 ok | 19 ok, 1 break |
| Итог в passed.csv | **20** | **20** (V11 прошёл со 2-й замены) |
| Новая съёмка | 1 (5%) | 2 (10%) |
| Углов | 18 | 18 |

Для сравнения, v2 (тот же скилл, но автор ещё не знал о проверке связки): там было по 2 отказа FLOW на прогон.
В v3 автор вычёркивал хуки, которые ломают связку, ещё на этапе идей (см. `ideas.md`).

---

## 01 — B03 "Morning rush"

### Запрос дизайнера (как есть)

```
REQUEST: New hooks for this winner, please. Body ID B03.
---
SockLock B03 "Morning rush" - 24s, 9:16

0:00-0:03 HOOK
VO: It's 7:45 and I have exactly one sock.
TEXT: 7:45. One sock.
SHOT: me hopping around the hallway in one sock, kid yelling in the background

0:03-0:08
VO: Every morning I dig through a basket of strangers.
TEXT: The basket of strangers
SHOT: pile of odd socks on the bed

0:08-0:13
VO: Then my sister sent me socks that snap together.
TEXT: Wait, they snap?
SHOT: close-up of the cuffs snapping together

0:13-0:19
VO: Off the feet, snap, into the wash, still a pair.
TEXT: Still a pair
SHOT: joined pair in the washer, comes out connected

0:19-0:24 CTA
VO: Take the quiz, five pairs for $29, cancel anytime.
TEXT: 5 pairs - $29
SHOT: end card with the quiz on a phone
```

### Как скилл понял сценарий (parse.md)

| segment | VO | on-screen | shot | что на кадре |
|---|---|---|---|---|
| hook | It's 7:45 and I have exactly one sock. | 7:45. One sock. | S01 | хопает по коридору в одном носке (проблема) |
| scene_1 | Every morning I dig through a basket of strangers. | The basket of strangers | S02 | куча непарных носков на кровати (проблема) |
| scene_2 | Then my sister sent me socks that snap together. | Wait, they snap? | S03 | манжеты защёлкиваются (продукт) |
| scene_3 | Off the feet, snap, into the wash, still a pair. | Still a pair | S04 | пара в стирке (продукт) |
| cta | Take the quiz, five pairs for $29, cancel anytime. | 5 pairs - $29 | S05 | энд-кард с квизом (продукт) |

Область: **только хук**, потому что в запросе «New hooks». Каждый хук должен вести в «Every morning I dig through a basket of strangers.»

### Результат: 20 из 20

Сцены 1–3 и CTA остаются оригинальными, меняются только хук, его текст на экране и первый кадр.

| id | угол | хук (VO) | текст на экране | кадр |
|---|---|---|---|---|
| V01 | math | I own 40 socks and zero pairs. | 40 socks. 0 pairs. | S02 |
| V02 | confession | Confession: I wore two different socks to work. | Two different socks. At work. | S01 |
| V03 | confession | I'm a grown adult who can't find socks. | Grown adult. No socks. | S01 |
| V04 | skeptic | I didn't think socks could fix my mornings. | Socks fixing mornings? Sure. | S01 |
| V05 | parent | Three kids, six loads, zero matching socks. | 3 kids. 0 pairs. | S02 |
| V06 | humor | Today I interviewed every sock in my basket. | Sock interviews: day one | S02 |
| V07 | humor | My sock basket needs a missing persons unit. | Missing: one sock. Again. | S02 |
| V08 | question | When did you last wear a matching pair? | Last matching pair? | S01 |
| V09 | relationship | My husband thinks I lose socks on purpose. | He thinks it's on purpose | S01 |
| V10 | hack | My worst morning habit had a silly fix. | Worst habit, silly fix | S01 |
| V11 | gift | Socks as a gift? Hear me out. | Socks as a gift? | S02 |
| V12 | morning-rush | Late again, and it's the socks' fault. | Late. Blame the socks. | S01 |
| V13 | mystery | Socks go in as pairs. Never come out. | In as pairs. Out alone. | S02 |
| V14 | *news-report* | Breaking: another sock vanished from this house overnight. | BREAKING: sock missing | S01 |
| V15 | *list* | Things I lose daily: keys, patience, socks. | Keys. Patience. Socks. | S01 |
| V16 | *dare* | I dare you to find one pair here. | Find one pair. Dare you. | S02 |
| V17 | *nostalgia* | Remember when socks came in pairs? | Socks used to have partners | S02 |
| V18 | *trip* | Packing for a trip. Found eleven single socks. | Packing: 11 single socks | **NEW**: открытый чемодан на кровати, руки кидают туда непарные носки |
| V19 | *moving* | Moved apartments. Found 23 socks. Zero pairs. | Moving day: 23 singles | S02 |
| V20 | *review* | One star for my sock basket. Here's why. | 1-star review: my basket | S02 |

*Курсив* — собственные углы скилла, которых нет в angles.md.

Отказов нет. Пограничные случаи, которые ревьюер пропустил:
- **V09:** муж больше не появляется в ролике.
- **V11:** обещание «Hear me out» окупается только во 2-й сцене («my sister sent me socks»).
- **V02:** текст «At work» стоит на кадре, где героиня дома в коридоре.

### Что посмотреть глазами в 01
- **V02 «At work»** поверх кадра дома. Ревьюер посчитал это нормальным (признание о прошлом), но на монтаже может читаться странно.
- **V09 «My husband…»** подразумевает, что рассказчица — женщина. В сценарии пол не указан, это надо сверить с актрисой.
- **V18 — единственная новая съёмка.** Лимит теперь 25%, но скилл взял 5%. Проверка связки отсекает «ситуационные» хуки (собака, свидание, отпуск), которые тело не подхватывает. Поэтому при области «только хук» новых сцен мало. Если нужно больше, проси область «хук + все тексты на экране»: тексты в сценах могут продолжать ситуацию из хука.
- **Цифры в хуках** (40 носков, 23 носка, 11 носков, «six loads»): это подсчёты от первого лица, brand.md такое разрешает. Но это всё равно выдумка, решай, нормально ли это для бренда.

---

## 03 — SL_B05_skeptic (грязный, только VO)

### Запрос дизайнера (как есть)

```
REQUEST: no timecodes sorry, just the voiceover from the editor. it's the skeptic one that's scaling, id SL_B05_skeptic. hooks pls
---
ok so I thought socks with magnets were the dumbest thing on the internet
like who needs that
but I had 30 single socks in a bag in my closet I'm not kidding
so I ordered them to prove a point
you take them off and the cuffs just snap together
I've washed them like twenty times and they still come out as a pair
my drawer actually looks like an adult lives here now
and they ship you five more pairs every three months
take the little quiz, it's five pairs for 29 bucks, you can cancel whenever
```

### Как скилл понял сценарий (parse.md)

Все кадры — **догадки**: в сценарии нет визуала.

| segment | VO | shot | что на кадре (догадка) |
|---|---|---|---|
| hook | ok so I thought socks with magnets were the dumbest thing on the internet | S01 | говорящая голова, скептичное лицо, носков в кадре нет (проблема) |
| scene_1 | like who needs that | S01 | та же голова, закатывает глаза (проблема) |
| scene_2 | but I had 30 single socks in a bag in my closet I'm not kidding | S02 | достаёт из шкафа мешок непарных носков (проблема) |
| scene_3 | so I ordered them to prove a point | S03 | заказ на телефоне / посылка (продукт) |
| scene_4 | you take them off and the cuffs just snap together | S04 | манжеты защёлкиваются (продукт) |
| scene_5 | I've washed them like twenty times and they still come out as a pair | S05 | пара из стирки (продукт) |
| scene_6 | my drawer actually looks like an adult lives here now | S06 | аккуратный ящик (продукт) |
| scene_7 | and they ship you five more pairs every three months | S07 | коробка подписки (продукт) |
| cta | take the little quiz, it's five pairs for 29 bucks, you can cancel whenever | S08 | энд-кард (продукт) |

Решения скилла:
- **Граница хука.** Хук — вся первая строка, хотя в ней 14 слов: естественной паузы нет.
- **Связка с телом.** scene_1 «like who needs that» и scene_3 «so I ordered them» требуют, чтобы хук называл носки и сохранял скептичный тон.
- **Предупреждения check.py про исходник:** хук говорит «magnets» и длиннее лимита (14 слов при максимуме 8).

### Результат: 20 из 22

| id | угол | хук (VO) | текст на экране | кадр |
|---|---|---|---|---|
| V01 | skeptic | My feed kept pushing un-losable socks. | My feed won't stop | S01 |
| V02 | skeptic | Socks you can't lose? I rolled my eyes. | Socks you can't lose? | S01 |
| V03 | confession | Confession: I roasted lost-proof socks online. | Confession: I was a hater | S01 |
| V04 | confession | I swore I'd never buy gimmick socks. | Never buying gimmick socks | S01 |
| V05 | mystery | Lost sock mystery, solved by... more socks? | Solved by more socks? | S02 |
| V06 | hack | Coworker's best life hack: socks that stay paired. | Her best hack? Socks. | S01 |
| V07 | hack | Every life hack account pushed the same socks. | Another 'life hack' | S01 |
| V08 | humor | Someone made socks with serious trust issues. | Socks with trust issues | S01 |
| V09 | humor | Someone sells socks the dryer can't eat. | The dryer can't eat these | **NEW**: носок падает в тёмный барабан сушилки |
| V10 | relationship | My roommate kept sending me this sock ad. | Roommate, stop sending this | S01 |
| V11-r2 | gift | Socks that can't get lost? Gag gift, surely. | Gag gift, surely? | S01 |
| V12 | question | Seen those socks that can't get lost? | Seen these socks yet? | S01 |
| V13 | *news-format* | Breaking: socks that never lose their partner. | BREAKING: sock news | S01 |
| V14 | *bet* | My brother bet me lost-proof socks work. | The sock bet | S01 |
| V15 | *group-chat* | Group chat verdict on un-losable socks: ridiculous. | Group chat says: ridiculous | S01 |
| V16 | *late-night-scroll* | Midnight scroll: socks that can't get lost. | Midnight scroll find | **NEW**: свет экрана на лице в тёмной спальне, экран не виден |
| V17 | *grandma* | Grandma asked if un-losable socks exist. | Grandma's sock question | S01 |
| V18 | *denial* | Someone engineered socks for a problem I ignored. | A problem I ignored | S02 |
| V19 | *comment-reply* | Someone commented: just buy the lost-proof socks. | Replying to that comment | S01 |
| V20 | *gym-bro* | Gym guy says his socks can't get lost. | Gym bro sock advice | S01 |

### Что отклонено и как исправлено (FLOW)

| раунд | хук | причина ревьюера |
|---|---|---|
| V11 (0) | My sister wants lost-proof socks for Christmas. | правило 2: начинается история про подарок, но сестра и Рождество больше не появляются, а тело про покупку для себя («to prove a point») |
| V11-r1 (1) | Gift guide pick: socks that can't get lost. | правило 3: рассказчица сама рекомендует носки и в следующей строке над ними смеётся («like who needs that») |
| V11-r2 (2) | Socks that can't get lost? Gag gift, surely. | **ok**: та же скептичная насмешка, «that» указывает на носки |

### Что посмотреть глазами в 03
- **Сначала таблица разбора.** Все кадры придуманы. Если на S01 (говорящая голова) видны носки или телефон с рекламой, 16 хуков открываются не на том кадре.
- **Однообразие.** Описание продукта повторяется почти в каждом хуке: «un-losable / lost-proof / can't get lost / stay paired / never lose their partner» — 13 из 20. Четыре хука начинаются с «Someone…» (V08, V09, V18, V19). Причина в теле: после хука идёт «like who needs that», поэтому хук обязан назвать вещь, и это почти всегда одно и то же описание. Правила и ревьюер этого не ловят, повторы видны только глазами.
- **Обещание пользы в хуке.** «can't get lost», «stay paired» — это не механика (слов magnet / snap нет), правила это пропускают. Но фактически это обещание продукта до раскрытия в теле. Исходный хук делал так же («socks with magnets»). Решай, нормально ли это.
- **Все хуки скептические.** Подарок, родитель и утренняя спешка в это тело не влезают, на них и пришлись все отказы. Это свойство тела, а не ошибка скилла. Но при таком теле правило «≥5 углов» выполняется за счёт обёрток вокруг одной позиции скептика.
- **Пограничные случаи, которые ревьюер пропустил:**
  - V09: «The dryer can't eat these» стоит на кадре, где носок как раз падает в сушилку.
  - V17: «Grandma asked…» → «like who needs that» требует додумать «а я сказала».
  - V05: хук на S02 показывает мешок носков раньше, чем scene_2 его «раскрывает».

---

## Замечания самих агентов к SKILL.md (повторяются из прогона в прогон)

1. **Область.** Неясно, означает ли «hooks» уровень «только хук» или это просто общая просьба. Оба автора выбрали «только хук». Если по умолчанию должно быть «хук + все тексты на экране», это надо прописать.
2. **Граница хука без паузы.** Если первая фраза слишком длинная и паузы нет, что делать, не сказано (03).
3. **Пол и роль рассказчика** в сценарии обычно не указаны. Хуки с «my husband», «mom of four» на это опираются, и ревьюер такое не ловит.
4. **Тело ограничивает выбор углов.** Если scene_1 зависит от хука, часть углов из angles.md физически не подходит. SKILL.md об этом молчит.

## Файлы
- [01_timecoded_v3/](01_timecoded_v3/): parse.md, ideas.md (44 идеи), candidates.json, passed.md/csv, flow_review.md, flow.json
- [03_dirty_vo_only_v3/](03_dirty_vo_only_v3/): то же, плюс rejected.md с двумя FLOW
