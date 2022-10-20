class PeopleDataRouter:
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == "people_data":
            return False

        return None
