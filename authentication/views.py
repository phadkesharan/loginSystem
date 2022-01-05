from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from loginSystem import settings
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_bytes, force_text
from .tokens import generate_token
from django.core.mail import EmailMessage

# Create your views here.

def home(request):
    return render (request, 'authentication/index.html')

def signup(request):

    if request.method == "POST":
        username = request.POST['username']
        firstname = request.POST['firstname']
        lastname = request.POST['lastname']
        email = request.POST['emailid']
        password = request.POST['password']
        passwordverify = request.POST['passwordverify']

        myUser = User.objects.create_user(username=username, email=email, password=password)
        myUser.first_name = firstname
        myUser.last_name = lastname
        myUser.is_active = False

        if len(User.objects.filter(username=username)) > 1:
            messages.error(request, "Username already exists!! Use other Username")
            myUser.delete()
            return redirect("home")

        if len(User.objects.filter(email=email)) > 1:
            messages.error(request, "Email already Exists!! Use other Email ID")
            myUser.delete()
            return redirect("home")

        if len(username) > 10:
            messages.error(request, "Username must be under 10 characters!")
            myUser.delete()
            return redirect("home")

        if password != passwordverify:
            messages.error(request, "Passwords do not match!!")
            myUser.delete()
            return redirect("home")

        if not username.isalnum():
            messages.error(request, "username should be alpha Numeric")
            myUser.delete()
            return redirect("home")

        myUser.save()
        messages.success(request, "Your Account has been successfully created! Please verify your Email to activate the account")

        #Welcome Email
        subject = "Welcome to MySiteLogin"
        message = "Hello" + myUser.first_name + "!!\n" + "Thank You for Signing on to out website\n" + "please verify your email id through verification email sent to you"
        from_email = settings.EMAIL_HOST_USER
        to_list = [myUser.email]
        send_mail(subject, message, from_email, to_list, fail_silently=False)

        #Confirm Email
        current_site = get_current_site(request)
        email_sub = "Confirm your Email! MySiteLogin"
        email_message = render_to_string("confirmation_email.html", {
            "name": myUser.first_name,
            "domain": current_site.domain,
            "uid": urlsafe_base64_encode(force_bytes(myUser.pk)),
            "token" : generate_token.make_token(myUser),
        })

        email = EmailMessage(
            email_sub,
            email_message,
            settings.EMAIL_HOST_USER,
            [myUser.email],
        )

        email.failsilently = True
        email.send()

        return redirect("signin")

    return render (request, 'authentication/signup.html')

def signin(request):

    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        print(user)
        if user is not None:
            login(request, user)
            fname = user.first_name
            messages.success(request, "Login Successfull!!")
            return render(request, "authentication/index.html", context={'firstname': fname})

        else:
            print("cannot login!")
            messages.error(request, "Bad Credentials")
            return redirect("home")

    return render(request, "authentication/signin.html")

def signout(request):

    logout(request)
    messages.success(request, "user logged out succcessfully!!")

    return redirect("home")


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        myUser = User.objects.get(pk=uid)

    except(TypeError, User.DoesNotExist, ValueError, OverflowError):
        myUser = None

    if myUser is not None and generate_token.check_token(myUser, token):
        myUser.is_active = True
        myUser.save()

        login(request, myUser)

        return redirect("home")

    else:
        return render(request, "activatation_failed.html")