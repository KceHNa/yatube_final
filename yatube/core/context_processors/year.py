import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    now = datetime.datetime.now().year
    return {
        'year': now
    }
