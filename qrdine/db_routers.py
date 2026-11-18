"""
Database router for the Cycle 1+ two-database architecture.
  default → control plane (users, restaurants, categories, menu items)
  tenant  → tenant data   (orders, customers)
"""


class ControlPlaneRouter:
    control_apps = {
        'admin', 'auth', 'contenttypes', 'sessions',
        'messages', 'staticfiles', 'sitemaps',
        'cloudinary_storage', 'storages', 'cloudinary',
        'accounts', 'restaurants', 'superadmin', 'menu', 'core',
    }

    tenant_apps = {'orders'}

    def db_for_read(self, model, **hints):
        return 'tenant' if model._meta.app_label in self.tenant_apps else 'default'

    def db_for_write(self, model, **hints):
        return 'tenant' if model._meta.app_label in self.tenant_apps else 'default'

    def allow_relation(self, obj1, obj2, **hints):
        return obj1._state.db == obj2._state.db

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == 'tenant':
            return app_label in self.tenant_apps
        if db == 'default':
            return app_label in self.control_apps
        return False