from helpers import render


def aboutus(request):
    return render(request, {}, 'news/aboutus.html')

def help(request):
    return render(request, {}, 'news/help.html')


def buttons(request):
    return render(request, {}, 'news/buttons.html')

