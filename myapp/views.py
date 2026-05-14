from django.shortcuts import render, HttpResponse, get_object_or_404, redirect
from .models import Hospital, User, Patient,Doctor, Appointment
from django.contrib.auth.hashers import make_password
from django.contrib import messages
import random
import string


# Create your views here.
# def login(request):
#     return render(request,"login.html")

def about(request):
    return HttpResponse("About page")

def home(request):
    return render(request,"home.html")

def doctor_dashboard(request):
    return render(request,"doctor_dashboard.html")

def patient_dashboard(request):
    return render(request,"patient_dashboard.html")

def login(request):
    if request.method == "POST":
        form_email     =   request.POST.get("email")
        password  = request.POST.get("password")
        print(form_email, password)
        try:
            user =  User.objects.get(email = form_email )
    
            print(user.password)            
        
            if password==user.password:
                print(user.username)
                print("LOGIN SUCCESSFUL")
                request.session["user"] = user.username
                request.session["email"] = user.email
                request.session["role"] = user.role
                # return redirect('index')
            
                if user.role=="DOCTOR":
                    return redirect("doctor_dashboard")
                elif user.role=="PATIENT":
                    return redirect("patient_dashboard")
            else:
                print("invaild password")
                messages.error(request, "Invalid Password")
                return redirect('login')
            
        except:
            print("not found")
           
            messages.error(request, "Patient with this email does not exist")
            return redirect('login')
     
    return render(request, "login.html")

def patient_register(request):
    if request.method == "POST":
        age =        request.POST.get("age")
        gender =    request.POST.get("gender")
        blood_group =   request.POST.get("blood_group")
        medical_history =   request.POST.get("medical_history")

        Patient.object.create(
            age = age,
            gender = gender,
            blood_group = blood_group,
            medical_history = medical_history
            
        )
        print("student data added successfully")
        return redirect('login')
    return render(request, "patient_register.html")

def doctor_register(request):

    hospitals = Hospital.objects.all()

    if request.method == "POST":
        hospital_id = request.POST.get("hospital_id")
        age = request.POST.get("age")
        specialization = request.POST.get("specialization")
        experience_years = request.POST.get("experience_years")
        fees = request.POST.get("fees")
        bio = request.POST.get("bio")


        Doctor.objects.create(
            hospital_id=hospital_id,
            age=age,
            specialization=specialization,
            experience_years=experience_years,
            fees=fees,
            bio=bio
        )

        return redirect("login")

    return render(request, "doctor_register.html")

def index(request):
    if not request.session.get('user'):
        return redirect('login')

    return HttpResponse(request, "done")

def logout(request):
    request.session.flush()

    return redirect('login')

def reset_password(request):
    if request.method=="POST":
        email = request.POST.get('email')
        try:
            user = user.objects.get(email = email)

            characters = string.ascii_letters+string.digits
            new_password=""
            for i in range(1,9):
                new_password += "".join(random.choices(characters))
            new_password = "1234"
            user.password = make_password(new_password)
            user.save()
            SEND_MAIL(
                'New Password',
                f'Your new password is {new_password}',
                'kbajaj0334@gmail.com',
                [email]
            )
        except:
            print("invalid mail")
            
    return redirect('login')

def hospital_profile(request):
    if request.method == "POST":
        name =   request.POST.get("name")
        address =   request.POST.get("address")
        city =      request.POST.get("city")
        state =     request.POST.get("state")
        phone_number = request.POST.get("phone_number")
        email =    request.POST.get("email")
 
        hospital_profile.objects.create(
            name = name,
            address = address,
            city =   city,
            state = state,
            phone_number = phone_number,
            email = email
        )
        print("data added successfully")

    return render(request, "hospital_profile.html")

