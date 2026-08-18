# IRI real-case review

Это не синтетический кейс: `packet_redacted.md` получен из реального снимка
заявки и сохраняет его структуру и содержимое. Перед публикацией из него
удалены имена и фамилии, суммы, даты, название проекта, URL, хэши и имена
файлов. Равенство/различие значений сохраняется стабильными placeholder-ами.
Даже этот обезличенный packet и OCR хранятся в Git как `git-crypt` ciphertext;
в открытом репозитории их содержимое не читается.

Сырые документы и gold не находятся в открытом репозитории. Gold подключается только
локальным путём:

```bash
docbench run --bench iri_review \
  --model minimax-m2.7 \
  --cases cases/iri-review/private/iri_real_private.yaml \
  --gold cases/iri-review/private/iri_real_gold.yaml
```

Перед локальным запуском приватного checkout:

```bash
base64 -d ~/whitetransport-gitcrypt.key.b64 | git-crypt unlock -
```

Ключ не хранится в репозитории и не должен попадать в логи, transcript или
аргументы команд, кроме stdin этой команды.

Файл gold должен содержать `case_id` и список `findings` с `id`, `field` и
внутренними `match_groups`. Он не передаётся модели, не копируется в transcript
и не попадает в результаты кроме агрегированных `gold_points`/`gold_max`.

`iri_real_redacted.yaml` — публичный smoke-fixture для проверки загрузки; он не
содержит private evidence и не предназначен для итоговой оценки.

Для публичного CI используйте только проверку загрузки и JSON-парсера без
private gold. Для настоящей оценки запускайте private packet + private gold на
локальной машине и публикуйте только агрегаты без transcript.

Механизм приватности общий для всех бенчмарков: добавьте `private: true` в
manifest кейса. Если в запуске есть хотя бы один такой кейс, полный transcript
всего запуска (включая реальные prompts и ответы) сохраняется только как
`transcript.json.gitcrypt`; для обычных кейсов остаётся `transcript.json`.
