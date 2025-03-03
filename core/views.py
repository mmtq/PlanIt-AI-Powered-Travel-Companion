from django.shortcuts import render
from Agent.Agent import TravelAgent
import logging, pyttsx3, json, os
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserForm, ProfileForm
from django.db import transaction
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount import providers
from allauth.socialaccount.providers.base import ProviderException
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings 

# from gtts import gTTS
# from django.core.files.storage import default_storage
# from tempfile import NamedTemporaryFile

# @csrf_exempt
# def read_blog(request):
#     if request.method == "POST":
#         data = json.loads(request.body)
#         content = data.get("content", "")        
#         # Create gTTS object
#         tts = gTTS(text=content, lang='en')  # Use 'en' for English, or change the language as needed
        
#         # Define the file path for the audio file (fixed name)
#         audio_file_path = os.path.join(settings.MEDIA_ROOT, "blog_audio.mp3")

#         # Save the audio file
#         tts.save(audio_file_path)

#         # Return the URL of the generated audio file
#         audio_url = os.path.join(settings.MEDIA_URL, "blog_audio.mp3")
#         return JsonResponse({"audio_url": audio_url})

#     return JsonResponse({"error": "Invalid request method"}, status=400)

@csrf_exempt
def read_blog(request):
    if request.method == "POST":
        data = json.loads(request.body)
        content = data.get("content", "")
        # content = "Hi, I am PlanIt. I will be your travel companion. How can I help you today?"
        
        if content:
            engine = pyttsx3.init()

            # Adjust speaking rate
            rate = engine.getProperty('rate')
            engine.setProperty('rate', 150)

            # Adjust volume
            engine.setProperty('volume', 1.0)

            # Change voice (female voice)
            voices = engine.getProperty('voices')
            engine.setProperty('voice', voices[1].id)

            audio_file_path = os.path.join(settings.MEDIA_ROOT, "blog_audio.mp3")
            engine.save_to_file(content, audio_file_path)
            engine.runAndWait()

            # Return the audio file URL
            audio_url = os.path.join(settings.MEDIA_URL, "blog_audio.mp3")
            return JsonResponse({"audio_url": audio_url})

        return JsonResponse({"error": "No content provided"}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=405)

logger = logging.getLogger(__name__)

# Initialize the TravelAgent as a global instance
travel_agent = TravelAgent()

@login_required
def index(request):
    context = {
        'messages': request.session.get('chat_history', []),
        'error': None
    }
    
    if request.method == "POST":
        try:
            user_message = request.POST.get('message', '').strip()
            if user_message:
                # Add user message to history
                chat_history = request.session.get('chat_history', [])
                chat_history.append({
                    'role': 'user',
                    'content': user_message
                })
                
                # Get AI response
                response = travel_agent.chat(user_message)
                
                if response:
                    chat_history.append({
                        'role': 'assistant',
                        'content': response
                    })
                    request.session['chat_history'] = chat_history
                    context['messages'] = chat_history
                else:
                    context['error'] = "Sorry, I couldn't generate a response. Please try again."
            else:
                context['error'] = "Please enter a message."
                
        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            context['error'] = "An error occurred. Please try again."
    
    return render(request, "index.html", context)

@login_required
def profile(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                user_form.save()
                profile_form.save()
            messages.success(request, 'Your profile was successfully updated!')
            return redirect('core:profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)

    # Get connected social accounts
    social_accounts = SocialAccount.objects.filter(user=request.user)
    connected_providers = [account.provider for account in social_accounts]

    # Get available providers
    available_providers = []
    provider_list = providers.registry.provider_map.values()
    for provider in provider_list:
        try:
            if provider.id not in connected_providers:
                available_providers.append({
                    'id': provider.id,
                    'name': provider.name,
                })
        except ProviderException:
            continue

    return render(request, 'core/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'social_accounts': social_accounts,
        'available_providers': available_providers,
        'connected_providers': connected_providers,
    })

