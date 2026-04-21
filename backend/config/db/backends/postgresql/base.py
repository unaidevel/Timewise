from django.db.backends.postgresql.base import (
    DatabaseWrapper as PostgreSQLDatabaseWrapper,
)


class DatabaseWrapper(PostgreSQLDatabaseWrapper):
    def get_connection_params(self):
        if self.settings_dict["NAME"] is None:
            maintenance_database = self.settings_dict["TEST"].get("MAINTENANCE_DB")
            if maintenance_database:
                self.settings_dict["NAME"] = maintenance_database

        return super().get_connection_params()
