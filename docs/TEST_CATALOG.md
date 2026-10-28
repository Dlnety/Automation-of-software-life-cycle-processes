# Каталог тестов ЛР7

Фикстуры перед каждым случаем включают DEMO_MODE=1, восстанавливают данные и запрещают реальные подключения к Oracle.

Общие данные: student_data — Казакова Диана, 2026, очная, группа 1; curriculum_data — специальность 1, дисциплина 2, семестр 4, 144 часа, экзамен; grade_data — студент 3, дисциплина 1, период 2026/2027, семестр 3, оценка 4. Учётные записи: study/study123 и teacher/teacher123 из тестового наполнения проекта.

Каждая строка параметризации выполняется как отдельный случай. Полный список развёрнутых случаев и результатов находится в evidence/junit.xml и evidence/python-run.txt.

## tests/integration/test_web.py

| Тест | Данные / параметры | Ожидаемый результат |
|---|---|---|
| `test_health` | Фикстуры: client | /health доступен без входа и возвращает контракт HTTP 200 + JSON. |
| `test_anonymous_redirect` | 'path': ['/', '/academic', '/academic/students', '/academic/students/1/edit', '/academic/curriculum', '/academic/curriculum/1/edit', '/teacher', '/teacher/grades', '/teacher/grades/1/edit'] | Гость не может открыть защищённые страницы. |
| `test_login_roles` | 'username, password, role, dashboard': [('study', 'study123', 'academic', '/academic'), ('teacher', 'teacher123', 'teacher', '/teacher')] | Обе роли проходят настоящую проверку хэша и получают свою стартовую страницу. |
| `test_bad_login` | 'username, password': [('study', 'wrong'), ('unknown', 'study123'), ('', '')] | Неверный пароль, неизвестный пользователь и пустая форма не дают сессию. |
| `test_logout` | Фикстуры: client, login | Выход очищает сессию и снова закрывает защищённые страницы. |
| `test_wrong_role_post` | 'username, password, path': [('teacher', 'teacher123', '/academic/students'), ('teacher', 'teacher123', '/academic/students/1/edit'), ('teacher', 'teacher123', '/academic/curriculum'), ('teacher', 'teacher123', '/academic/curriculum/1/edit'), ('study', 'study123', '/teacher/grades'), ('study', 'study123', '/teacher/grades/1/edit')] | POST другой роли запрещён и не меняет данные или аудит. |
| `test_academic_search` | Фикстуры: client, login | Форма аналитики выводит число студентов и сведения о дисциплине. |
| `test_discipline_missing` | Фикстуры: client, login | Неизвестная дисциплина даёт понятное сообщение. |
| `test_student_create_edit` | Фикстуры: client, login, student_data | Создание и редактирование студента проходят через HTTP и видны в списке; пишется аудит. |
| `test_student_invalid_http` | Фикстуры: client, login, student_data | HTTP-запрос с неверным годом показывает ошибку без сохранения. |
| `test_curriculum_create_edit` | Фикстуры: client, login, curriculum_data | Учебный план добавляется и редактируется, изменения и аудит сохраняются. |
| `test_duplicate_curriculum` | Фикстуры: client, login, curriculum_data | Повторный элемент плана отклоняется без второй записи и аудита. |
| `test_grade_create_edit` | Фикстуры: client, login, grade_data | Преподаватель добавляет и меняет оценку, журнал и аудит отражают результат. |
| `test_duplicate_grade` | Фикстуры: client, login, grade_data | Вторую оценку для той же тройки студент–дисциплина–период нельзя добавить. |
| `test_invalid_grade_http` | Фикстуры: client, login, grade_data | Оценка 6 для экзамена отклоняется через HTTP без записи. |
| `test_missing_record` | 'username, password, path, target, message': [('study', 'study123', '/academic/students/999/edit', '/academic/students', 'Студент не найден'), ('study', 'study123', '/academic/curriculum/999/edit', '/academic/curriculum', 'Элемент учебного плана не найден'), ('teacher', 'teacher123', '/teacher/grades/999/edit', '/teacher/grades', 'Запись журнала не найдена')] | Редактирование отсутствующей записи перенаправляет в список с сообщением. |

## tests/unit/test_transactions.py

| Тест | Данные / параметры | Ожидаемый результат |
|---|---|---|
| `test_add_student_transaction` | 'failure': [False, True] | Oracle-адаптер передаёт параметры, делает commit либо rollback и закрывает соединение. |

## tests/unit/test_validation.py

| Тест | Данные / параметры | Ожидаемый результат |
|---|---|---|
| `test_password_correct_and_wrong` | Данные создаются внутри теста | PBKDF2: верный пароль принимается, неверный отклоняется. |
| `test_password_malformed` | 'stored': ['', 'broken', 'sha1$1000$aa$bb', 'pbkdf2_sha256$abc$aa$bb', 'pbkdf2_sha256$1000$zz$bb', 'pbkdf2_sha256$0$aa$bb'] | Повреждённые хэши не приводят к успешному входу или исключению. |
| `test_next_id` | 'rows, expected': [([], 1), ([{'id': 7}, {'id': 2}], 8)] | Идентификатор больше максимального, для пустой таблицы равен 1. |
| `test_full_name` | 'middle, expected': [('Иванович', 'Иванов Иван Иванович'), ('', 'Иванов Иван'), (None, 'Иванов Иван')] | ФИО собирается без лишнего пробела при отсутствии отчества. |
| `test_curriculum_invalid` | 'field, value, message': [('semester', '0', 'Семестр'), ('semester', '13', 'Семестр'), ('hours', '0', 'Количество часов'), ('hours', '-1', 'Количество часов'), ('report_type', 'контрольная', 'форма отчётности')] | Семестр вне 1–12, неположительные часы и неизвестная отчётность отклоняются. |
| `test_curriculum_boundaries` | 'semester': ['1', '12'] | Граничные допустимые семестры 1 и 12 принимаются. |
| `test_invalid_student_no_write` | 'field, value, message': [('form', 'дистанционная', 'форма обучения'), ('year', '1999', 'Год поступления'), ('year', '2101', 'Год поступления'), ('group_id', '999', 'группа не найдена')] | Некорректный студент отклоняется без записи студента и аудита. |
| `test_count_students` | 'form, expected': [('очная', 2), ('очно-заочная', 1), ('заочная', 0)] | Подсчёт по каждой допустимой форме соответствует исходным данным. |
| `test_count_rejects_unknown_form` | Данные создаются внутри теста | Подсчёт отклоняет неизвестную форму обучения. |
| `test_valid_grade` | 'student, discipline, grade': [(1, 1, '2'), (1, 1, '5'), (2, 1, 'зачет'), (2, 1, 'незачет')] | Экзамен принимает 2–5, зачёт принимает зачет/незачет. |
| `test_invalid_grade` | 'student, discipline, grade': [(1, 1, '1'), (1, 1, '6'), (1, 1, 'зачет'), (2, 1, '5'), (999, 1, '5'), (1, 999, '5')] | Неверная шкала, отсутствующий студент или учебный план отклоняются. |
| `test_friendly_error` | 'text, expected': [('ORA-20001: Дисциплина отсутствует\nORA-06512: details', 'Дисциплина отсутствует'), ('ORA-00001: details', 'Такая запись уже существует.'), ('ORA-02291: details', 'Не найден связанный объект. Проверьте выбранные значения.'), ('ORA-02290: details', 'Одно из значений не соответствует допустимым ограничениям.'), ('internal connection info', 'Операцию выполнить не удалось. Проверьте введённые данные.')] | Ошибки Oracle преобразуются в понятные сообщения без внутренних деталей. |

