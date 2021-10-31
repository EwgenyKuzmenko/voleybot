from db_router import routes

class defaultFileScan(object):

    def db_for_read(self, model, **hints):
        for route in routes.keys():
            if model._meta.object_name in routes[route]:
                return route
        return 'default'

    def db_for_write(self, model, **hints):
        for route in routes.keys():
            if model._meta.object_name in routes[route]:
                return route
        return 'default'
    
    def allow_relocation(self, obj1, obj2, **hints):
        for route in routes.keys():
            if obj1._meta.object_name in route[route] and obj2._meta.object_name in route[route]:
                return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        for route in routes.keys():
            for obj_ in routes[route]:
                if db == route and model_name == obj_.lower():
                    return True
        return db == "default"