# ЛР7. Тесты StudentProgress

Комплект подготовлен по архиву ветки dev, коммит e9f9063e623cb5bdd568747f5db8233866e256be.
Исходные app.py, db.py, Dockerfile и Compose не изменены. В архиве дополнения
только новые файлы: tests/, ci/Dockerfile.tests, ci/run_tests.sh,
requirements-test.txt, pytest.ini и docs/.
Если на TEST код уже отличается от присланного, сначала проверяем совместимость запуском тестов.

## 1. Что проверяется

Использованы pytest и pytest-cov. 78 случаев: 44 юнит и 34 интеграционных.
Юнит-тесты проверяют отдельные функции db.py: пароли, ошибки, валидацию,
подсчёт, ФИО, идентификаторы. В двух случаях Oracle-подключение заменено
MagicMock, чтобы проверить параметры вызова процедуры, commit, rollback и close.
Это юнит-проверка адаптера, а не проверка работающей Oracle.

Интеграционные тесты выполняют HTTP-запросы через Flask test_client;
работают настоящие маршруты, сессии, PBKDF2, функции db.py и шаблоны Jinja.
DEMO_MODE=1 использует предусмотренное приложением хранилище в памяти.
Бизнес-функции не подменяются. Данные и аудит восстанавливаются перед каждым
тестом; случайное подключение к Oracle запрещено фикстурой.

Oracle, PL/SQL, SQL-ограничения, триггеры, долговременное хранение и сеть этим
набором не проверяются. Для них нужен отдельный запуск на тестовой Oracle.
Для выполнения данного набора включать STAGE и PROD-ВМ не требуется.

Описание каждой тестовой функции, параметров и ожидаемых результатов:
[TEST_CATALOG.md](TEST_CATALOG.md). Параметризованные строки — отдельные случаи pytest.

## 2. Перенос на TEST

Скачай studentprogress-lr7-tests.zip в папку Downloads на TEST.
Если скачала на основной ноутбук, перенеси архив в TEST через общую папку VirtualBox.
Включи только TEST. Сначала выполни:

```bash
cd ~/studentprogress-lr5
git status
git branch --show-current
```

cd открывает проект, status показывает несохранённые изменения, последняя
команда показывает ветку. Если есть изменения ЛР6, сначала сохрани их отдельным
коммитом, проверив список файлов. Не переключай ветку и не используй reset --hard.
Новая ветка должна начинаться от актуального кода, содержащего нужные изменения ЛР6.
Когда состояние чистое и исходная ветка проверена:

```bash
git switch -c feature/lr7-tests
mkdir -p ~/lr7-package
unzip ~/Downloads/studentprogress-lr7-tests.zip -d ~/lr7-package
cp -r ~/lr7-package/tests ./
mkdir -p ci docs
cp ~/lr7-package/ci/Dockerfile.tests ci/
cp ~/lr7-package/ci/run_tests.sh ci/
cp ~/lr7-package/requirements-test.txt ~/lr7-package/pytest.ini ./
cp -r ~/lr7-package/docs/. docs/
git status --short
```

switch -c создаёт рабочую ветку, unzip распаковывает комплект отдельно,
cp переносит тесты и инструкции в проект. Существующие файлы ci/ ЛР6 сохраняются.
Если tests/ или pytest.ini уже есть, сначала сравни их с комплектом, не копируй поверх вслепую.
Если архив лежит не в Downloads, замени только путь к архиву.

## 3. Локальная проверка в Docker

Из корня проекта:

```bash
bash ci/run_tests.sh unit
bash ci/run_tests.sh integration
```

Первый запуск собирает Python 3.12 и ставит зависимости, поэтому может занять
несколько минут. Второй использует кэш Docker. Скрипт создаёт контейнер,
выполняет pytest, копирует XML-отчёты и удаляет контейнер. Результат каждого
набора лежит в test-reports/unit/ или test-reports/integration/.
Код возврата pytest сохраняется: упавшая проверка делает шаг CI неуспешным.
Данные приложения на STAGE не затрагиваются.

Один общий запуск всех 78 случаев:

```bash
bash ci/run_tests.sh all
```

Для компьютера без Docker можно запустить те же тесты напрямую:

```bash
python3 -m venv .venv-lr7
source .venv-lr7/bin/activate
python -m pip install -r requirements-test.txt
python -m pytest -v --junitxml=test-reports/all/junit.xml --cov=app --cov=db --cov-report=term-missing --cov-report=xml:test-reports/all/coverage.xml
```

venv изолирует зависимости, pip устанавливает их, pytest запускает проверки;
--junitxml создаёт отчёт для CI, --cov измеряет выполнение строк двух модулей.
Фикстура задаёт DEMO_MODE независимо от локального .env.

Перед коммитом добавь в существующий .gitignore (создай, если его нет),
не удаляя его старые строки:

```gitignore
.venv-lr7/
__pycache__/
.pytest_cache/
.coverage
htmlcov/
test-reports/
```

Затем:

```bash
git add tests ci/Dockerfile.tests ci/run_tests.sh requirements-test.txt pytest.ini docs .gitignore
git diff --cached --stat
git commit -m "Add unit and integration tests for LR7"
git push -u origin feature/lr7-tests
```

add выбирает файлы, diff показывает состав коммита, commit сохраняет изменения,
push отправляет ветку на GitHub. Файлы .env не добавляй.

## 4. TeamCity

Настройку выполнить в существующей конфигурации сборки, а при нескольких
независимых конфигурациях — в каждой, которая выпускает приложение.
У агента уже должны работать Docker CLI и доступ к Docker daemon, как в ЛР5–6.
Скрипт не использует bind mount: исходники копируются при сборке, а отчёты —
через docker cp. Это подходит для агента, который сам работает в контейнере.

### Порядок шагов

1. Static Analysis — Pylint и Gitleaks (шаги ЛР6).
2. Сборка приложения: Docker Build и Docker Build FEATURE с прежними условиями веток.
3. Unit Tests — новый шаг для всех веток.
4. Integration Tests — новый шаг для всех веток.
5. Docker Push DEV / Docker Push PROD с прежними условиями веток.
6. Deploy to STAGE с прежним условием ветки.

Перенеси Docker Build FEATURE, который раньше был в конце, в блок сборки.
Тестовый образ скрипт собирает дополнительно: он включает pytest, в отличие от
образа приложения. Проверяется тот же checkout текущей ветки.

В Build Steps → Add build step выбери Command Line, Custom script:

Имя Unit Tests:

```bash
bash ci/run_tests.sh unit
```

Имя Integration Tests:

```bash
bash ci/run_tests.sh integration
```

Рабочая директория — корень checkout (поле можно оставить пустым).
Не добавляй к тестам условие teamcity.build.branch=dev или prod.
Для тестов и всех шагов публикации/деплоя выбери
If all previous steps finished successfully. При ненулевом коде теста доставка
должна пропускаться. Проверь Failure Conditions: включено падение сборки
при ошибке процесса и при упавшем тесте. Не добавляй `|| true` к тестовым командам.

### Ветки и автоматический запуск

В VCS Root проверь Branch specification:

```text
+:refs/heads/*
```

Default branch оставь существующим. В Branch filter конфигурации и VCS Trigger:

```text
+:*
```

VCS Trigger должен быть включён. Фильтр не поможет, если ветка исключена в VCS Root.
Ветка должна содержать сами тестовые файлы — после FEATURE они попадут в dev и prod
через принятый у вас процесс Pull Request/merge.

### Отчёты

Build Features → Add build feature → XML report processing.
Report type: Ant JUnit. Monitoring rules:

```text
+:test-reports/unit/junit.xml
+:test-reports/integration/junit.xml
```

coverage.xml не добавляй в обработчик JUnit: это другой формат.
В General Settings → Artifact paths сохрани правило ЛР6 и добавь:

```text
analysis-reports/** => static-analysis
test-reports/** => automated-tests
```

JUnit покажет отдельные проверки во вкладке Tests, XML покрытия останется артефактом.
При повторных запусках скрипт удаляет старые XML только выбранного набора.
Если используешь чистый checkout TeamCity, старые результаты также не останутся.

Официальные инструкции:
- https://www.jetbrains.com/help/teamcity/configuring-build-steps.html
- https://www.jetbrains.com/help/teamcity/cloud/xml-report-processing.html
- https://www.jetbrains.com/help/teamcity/working-with-feature-branches.html
- https://www.jetbrains.com/help/teamcity/branch-filter.html

## 5. Демонстрация плохого кода

Сначала получи зелёную сборку feature/lr7-tests. Не вноси демонстрационный дефект
в dev или prod. Проверь, что app.py не содержит несохранённых изменений:

```bash
git status
git diff --exit-code -- app.py
```

Оставаясь в feature/lr7-tests, открой app.py и в функции health поменяй только:

```python
"status": "ok"
```

на:

```python
"status": "broken"
```

Тесты не меняем. Локальная демонстрация:

```bash
bash ci/run_tests.sh integration
```

Ожидается: test_health FAILED, код процесса 1. Для скриншота TeamCity:

```bash
git add app.py
git commit -m "Demonstrate LR7 failure in health response"
git push
```

Дождись красной FEATURE-сборки и зафиксируй ошибку сравнения JSON.
Проверь, что публикация и развёртывание пропущены. Не вливай дефектный код.
Если этот коммит по-прежнему последний и других правок нет, исправь его:

```bash
git revert --no-edit HEAD
git push
```

revert создаёт новый коммит, отменяющий дефект без переписывания истории.
Дождись зелёной сборки, затем делай Pull Request в dev.
После переноса исправленной версии и тестов в dev и prod получи по зелёной
сборке для каждой ветки. Для этого не нужна отдельная PROD-ВМ: тесты идут на TEST.
Существующие шаги деплоя при этом следуют вашим настроенным условиям.
Не запускай PROD-деплой, если он ещё не настроен; выполнение тестов ветки prod
и развёртывание на PROD-стенд — разные действия.

## 6. Что осталось сделать у тебя

Здесь подтверждён прямой запуск Python 3.12: 78 passed, 0 failed, 0 skipped.
Проверена отдельная копия с дефектом health: 1 failed, exit code 1.
app.py исходного проекта не менялся. Логи находятся в docs/evidence/.
Docker в среде подготовки отсутствует: Dockerfile и shell-синтаксис проверены,
но реальную сборку контейнера нужно выполнить на TEST.
TeamCity и ВМ отсюда недоступны, поэтому успешные сборки веток и скриншоты
ещё не получены. Инструкции не являются подтверждением выполнения этих действий.

Для отчёта нужны скриншоты:
1. Два тестовых шага и их положение до Push/Deploy.
2. Branch specification и VCS Trigger для всех веток.
3. Зелёная FEATURE/FIX-сборка и вкладка Tests.
4. Зелёная dev-сборка и Tests.
5. Зелёная prod-сборка и Tests.
6. Красная FEATURE-сборка с test_health и пропущенными шагами доставки.
7. Артефакты JUnit и покрытия.

Основа текста отчёта: LR7_REPORT_DRAFT.md. Не называй её готовым отчётом до
добавления реальных результатов TeamCity, скриншотов и реквизитов группы.
