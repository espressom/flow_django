from django.shortcuts import render

# Create your views here.


def management_index(request):
    return render(request, 'management/index.html')


def management_login(request):
    return render(request, 'management/login.html')


def management_404(request):
    return render(request, 'management/404.html')


def management_forgot_password(request):
    return render(request, 'management/forgot_password.html')


def dump_button(request):
    return render(request, 'dump/button.html')


def dump_card(request):
    return render(request, 'dump/card.html')