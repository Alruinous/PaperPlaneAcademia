from django.apps import AppConfig


class PapersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'papers'

    def ready(self):
        """
        确保在应用启动时加载 signals 模块。
        """
        import papers.signals  # 确保正确导入