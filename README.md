## Запуск проекта

1. Запусти Docker Compose:

   ```bash
   docker-compose up --build
   ```

2. После успешного запуска:

   - **Auth Service**: [http://localhost:8000/auth](http://localhost:8000/auth)
   - **PgAdmin**: [http://localhost:5050](http://localhost:5050)

   Вход в pgAdmin с использованием следующих учетных данных:
   - Email: `admin@admin.com`
   - Password: `admin`

3. Чтобы подключиться к базе данных PostgreSQL, используй следующие параметры:

   - **Хост**: `db` (это имя сервиса базы данных в `docker-compose.yml`)
   - **Порт**: `5432`
   - **Имя базы данных**: `mydatabase`
   - **Имя пользователя**: `user`
   - **Пароль**: `password`

4. Очистка Docker окружения
Остановка всех контейнеров: `docker stop $(docker ps -a -q)`
Удаление всех контейнеров: `docker rm $(docker ps -a -q)`
Удаление всех образов: `docker rmi $(docker images -q)`
Полная очистка системы: `docker system prune -a --volumes -f`
