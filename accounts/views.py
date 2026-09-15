from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from .models import FitnessUser
from .forms import FitnessUserForm, RegisterForm, LoginForm


def get_current_fitness_user(request):
    uid = request.session.get('fitness_user_id')
    if not uid:
        return None
    return FitnessUser.objects.filter(id=uid).first()


def login_fitness_user(request, user):
    request.session['fitness_user_id'] = user.id


class FitnessLoginRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not get_current_fitness_user(request):
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)


class RegisterView(View):
    def get(self, request):
        if get_current_fitness_user(request):
            return redirect('dashboard')
        return render(request, 'registration/register.html', {'form': RegisterForm()})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login_fitness_user(request, user)
            from journal.services import FitnessRecommendationEngine
            FitnessRecommendationEngine(user).generate_recommendations()
            messages.success(request, "Реєстрація успішна. AI згенерувало вашу програму тренувань.")
            return redirect('workout_detail')
        return render(request, 'registration/register.html', {'form': form})


class LoginView(View):
    def get(self, request):
        if get_current_fitness_user(request):
            return redirect('dashboard')
        return render(request, 'registration/login.html', {'form': LoginForm()})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            login_fitness_user(request, form.fitness_user)
            messages.success(request, "Вхід виконано.")
            return redirect('dashboard')
        return render(request, 'registration/login.html', {'form': form})


class LogoutView(View):
    def post(self, request):
        request.session.flush()
        messages.info(request, "Ви вийшли з акаунту.")
        return redirect('home')


# Поля анкети, від яких залежать програма тренувань і раціон
PLAN_FIELDS = {
    'date_of_birth', 'weight', 'height', 'fitness_goal',
    'gender', 'focus_muscle_group', 'session_hours',
}


class ProfileEditView(FitnessLoginRequiredMixin, View):
    def get(self, request):
        user = get_current_fitness_user(request)
        form = FitnessUserForm(instance=user)
        return render(request, 'profile_edit.html', {'form': form, 'fitness_user': user})

    def post(self, request):
        user = get_current_fitness_user(request)
        form = FitnessUserForm(request.POST, instance=user)
        if form.is_valid():
            plan_changed = PLAN_FIELDS & set(form.changed_data)   # змінилось щось, від чого залежить програма
            form.save()
            if plan_changed:
                from journal.services import FitnessRecommendationEngine
                FitnessRecommendationEngine(user).generate_recommendations()
                messages.success(request, "Параметри оновлено. Програму й раціон перераховано під нові дані.")
            else:
                messages.success(request, "Параметри користувача успішно оновлено!")
            return redirect('dashboard')
        return render(request, 'profile_edit.html', {'form': form, 'fitness_user': user})