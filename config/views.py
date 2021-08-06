from django.shortcuts import render

def defaultPage(request):
    print('>>> default 접속 >>>')
    return render(request, "defaultPage.html")