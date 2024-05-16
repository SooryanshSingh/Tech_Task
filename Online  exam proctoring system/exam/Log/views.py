from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
def login_user(request):
	if request.method=="POST":
		username=request.POST['username']
		password=request.POST['password']
		user=authenticate(request,username=username,password=password)
		if user is not None:
			messages.success(request,"Login successful")
			login(request,user)
			return redirect('home')
		else:
			messages.error(request,("invalid information..."))
			return redirect('login')
	else:		
		return render(request, 'login.html',{})
def logout_user(request):
	logout(request)
	messages.success(request,("You were logged out"))
	return redirect('home')
	
	
def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
        	
   		
            user = form.save()
            username=form.cleaned_data['username']
            password=form.cleaned_data['password1']
            user=authenticate(username=username,password=password)  
            login(request, user)
            messages.success(request,"Registered")
            return redirect('home') 
    else:
        form = UserCreationForm()
    return render(request, 'signup.html', {'form': form})

# Create your views here.
