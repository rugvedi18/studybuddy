from multiprocessing import context
from unicodedata import name
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from .models import Room, Topic, Message, User
from .forms import RoomForm, UserForm, MyUserCreationForm


def loginPage(request):
    page = 'login'

    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
        except:
            messages.error(request, 'User does not exist')

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, 'Username or password does not exist')

    template_name = 'base/login_register.html'
    context = {'page': page}

    return render(request, template_name, context)


def logoutUser(request):
    logout(request)
    return redirect('index')


def registerUser(request):
    form = MyUserCreationForm()

    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('index')
        else:
            messages.error(request, 'An error occurred during registration')

    template_name = 'base/login_register.html'
    context = {'form': form}

    return render(request, template_name, context)


def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    )

    topics = Topic.objects.all()[0:5]
    room_count = rooms.count()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))

    template_name = 'base/home.html'
    context = {
        'rooms': rooms,
        'topics': topics,
        'room_count': room_count,
        'room_messages': room_messages,
    }

    return render(request, template_name, context)


def room(request, pk):
    room = Room.objects.get(id=pk)
    # get all the msgs specific to the above room
    # the message is the Model name and _set.all() is set of msgs
    room_messages = room.message_set.all()
    participants = room.participants.all()

    if request.method == 'POST':
        message = Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)

    template_name = 'base/room.html'
    context = {'room': room, 'room_messages': room_messages,
               'participants': participants}

    return render(request, template_name, context)


def userProfile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()  # get all the children of a object
    room_messages = user.message_set.all()
    topics = Topic.objects.all()

    template_name = 'base/profile.html'
    context = {'user': user, 'rooms': rooms,
               'room_messages': room_messages, 'topics': topics}

    return render(request, template_name, context)


@login_required(login_url='login')
def createRoom(request):
    form = RoomForm
    topics = Topic.objects.all()

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)

        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description'),
        )
        return redirect('index')

    template_name = 'base/room_form.html'
    context = {'form': form, 'topics': topics}

    return render(request, template_name, context)


@login_required(login_url='login')
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()

    if request.user != room.host:
        return HttpResponse('You are not allowd here!!')

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('room')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect('index')

    template_name = 'base/room_form.html'
    context = {'form': form, 'topics': topics, 'room': room}

    return render(request, template_name, context)


@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)

    if request.user != room.host:
        return HttpResponse('You are not allowd here!!')

    if request.method == 'POST':
        room.delete()
        return redirect('index')

    template_name = 'base/delete.html'

    return render(request, template_name, {'obj': room})


@login_required(login_url='login')
def deleteMessage(request, pk):
    message = Message.objects.get(id=pk)

    if request.user != message.user:
        return HttpResponse('You are not allowd here!!')

    if request.method == 'POST':
        message.delete()
        return redirect('index')

    template_name = 'base/delete.html'

    return render(request, template_name, {'obj': message})


@login_required(login_url='login')
def updateUser(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)

    template_name = 'base/update_user.html'
    context = {'form': form}

    return render(request, template_name, context)


def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)

    template_name = 'base/topics.html'
    context = {'topics': topics}

    return render(request, template_name, context)


def activityPage(request):
    room_messages = Message.objects.all()

    template_name = 'base/activity.html'
    context = {'room_messages': room_messages}

    return render(request, template_name, context)
