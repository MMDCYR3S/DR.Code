from django.apps import AppConfig


class QuestionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.questions"

    def ready(self):
        import apps.questions.signals.question_notify
