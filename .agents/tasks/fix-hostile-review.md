# Исправление hostile review

Результат: публичный русский срез не выдаёт разнородные либо cache-replay
измерения за единый ранжированный live-бенчмарк; каждая опубликованная ссылка
доступна и ведёт к provenance-артефакту.

Кратчайший canary: GitHub Pages `/russian/` и корень сайта дают только
существующие ссылки; русский срез явно показывает scope, режимы запуска и
не ранжирует несовместимые метрики.

1. Метрика и публичный UI — L; пути `docbench/leaderboard.py`,
   `scripts/publish_russian_leaderboard.py`, `docs/`; без новых model runs;
   проверка: HTML/asset tests. 10–18 min.
2. Provenance, cache/retry и scoring labels — L; пути `docbench/run.py`,
   `docbench/leaderboard.py`, tests; проверка: focused pytest. 10–18 min.
3. Immutable Docker и public-link canary — L; пути `Dockerfile`, docs/tests;
   проверка: Docker build + HTTP link checker. 8–15 min.

Неподтверждённые вопросы (gold/translation leakage, provider routing,
upstream ACE pin) не объявляются исправленными без нового первичного
доказательства; они будут маркированы как границы текущего claims scope.
