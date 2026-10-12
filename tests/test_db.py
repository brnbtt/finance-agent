from finance_bot.db import MIGRATIONS, Database, User, UserState


def test_migrations_apply_once_and_keep_data(tmp_path):
    path = tmp_path / "bot.db"
    first = Database(path)
    user = first.get_or_create_user("telegram", "1")
    first.update_user(user.id, UserState.READY, name="Bia")
    first.close()

    reopened = Database(path)

    assert reopened.schema_version == len(MIGRATIONS)
    assert reopened.get_or_create_user("telegram", "1") == User(user.id, "Bia", UserState.READY)
    reopened.close()
