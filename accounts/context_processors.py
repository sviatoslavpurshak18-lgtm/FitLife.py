from .models import FitnessUser


def current_fitness_user(request):
    uid = request.session.get('fitness_user_id')
    user = FitnessUser.objects.filter(id=uid).first() if uid else None
    return {'current_fitness_user': user}
