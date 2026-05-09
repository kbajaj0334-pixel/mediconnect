from django.shortcuts import render, HttpResponse


# Create your views here.
def login(request):
    return render(request,"login.html")

def about(request):
    return HttpResponse("About page")

def home(request):
    return render(request,"home.html")