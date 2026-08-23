# Fresh Russian subscription campaign

## Решение

**Результат:** заменить исторический русский срез свежими cache-cold онлайн-прогонами
MiniMax M2.5/M2.7/M3, GLM-4.7-Flash и одной конфигурацией Luna — `medium`.
`glm-4.5-air`, Yandex/Alice и GigaChat исключены. Метрики suite не агрегируются.

**Краткий canary:** для каждого из пяти маршрутов есть новый `results.json` с
`cache_mode=bypass`, сохранёнными ответами и успешным покрытием трёх русских suite;
Pages публикует только эту кампанию.

## Листы

1. **Fresh runs** — владелец Lead; 12/30 минут. Запустить 15 cache-cold online
   измерений в отдельном датированном каталоге. Проверка: complete case coverage,
   no provider errors, transcript receipt hashes. Не трогать платные маршруты.
2. **Publish** — владелец Lead; зависит от 1; 3/8 минут. Рендер русской Pages из
   нового каталога и проверить локальные ссылки. Не создавать общий рейтинг.
3. **Delivery** — владелец Lead; зависит от 2; 3/7 минут. Тесты, Docker, scoped
   commit/push и публичный Pages canary.

## Время

Цикл fresh-russian-subscription-campaign начат 2026-08-23T22:26:00+03:00.
Минимум 15, максимум 45 активных минут. Активное время контролируется вручную.

## Статус — 2026-08-23

**Не публиковать.** Первичный параллельный запуск дал `Errno 101 Network is
unreachable` в Python-клиенте. Проверка без ключа показывает доступность
`api.minimax.io` и OmniRoute по HTTP (`401` ожидаем), но TLS timeout Z.ai.
Последовательные retry частично восстанавливают MiniMax: M2.5 grant — 10/10,
policy — 12/12, ACE — только 5/30 (25 network errors). Следующий запуск должен
идти с сетевого runner'а, где стабильно проходит полный ACE canary; после этого
повторить ровно пять разрешённых маршрутов и только затем рендерить Pages.

## Повтор с provider-lane — 2026-08-24

Повторён отдельный `russian-20260824-subscription-fresh`: внутри MiniMax
`M2.5 → M2.7 → M3` последовательно; отдельно и параллельно — Z.ai GLM-4.7-Flash
и OmniRoute Luna medium. Все сохранённые локальные результаты имеют
`cache_mode=bypass`.

**Не публиковать.** MiniMax остаётся инфраструктурно невалиден даже без
внутрипровайдерского параллелизма (M2.5: grant 7 errors, policy 12, ACE 30;
M2.7/M3 аналогично). Luna дала полные grant 10/10 и policy 12/12, но одиночный
ACE вызов не завершился за 2.5 минуты и был остановлен вместе с зависшим Z.ai
grant. Локальные `var/runs/...` — намеренно ignored execution residue, а не
доказательство для Pages.
