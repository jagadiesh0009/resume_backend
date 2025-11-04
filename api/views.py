from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework import generics
from .models import Fruit
from .serializers import *
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from rest_framework.permissions import IsAuthenticated
from google.oauth2 import id_token
import requests
import google.generativeai as genai
from rest_framework.permissions import IsAuthenticated
from google.oauth2 import id_token
from google.auth.transport.requests import Request  
from .utils import *

User=get_user_model()

class FruitList(generics.ListCreateAPIView):
    queryset = Fruit.objects.all()
    serializer_class = FruitSerializer
class FruitOp(generics.RetrieveUpdateDestroyAPIView):
    queryset=Fruit.objects.all()
    serializer_class=FruitSerializer
    lookup_field='pk'

class Register(APIView):
    def post(self,request ):
        serializer=RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user=serializer.save()

            refresh = RefreshToken.for_user(user)
            token_data = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            return Response({
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email
                    },
                    "tokens": token_data
                }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ForgotPassword(APIView):
    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        email = serializer.validated_data['email']
        user = User.objects.filter(email=email).first()

        if not user:
            return Response({'error': 'User does not exist.'}, status=404)

        otp = get_random_string(length=6, allowed_chars='0123456789')

        
        cache.set(f'otp_{email}', otp, timeout=600)
        cache.set(f'email_for_otp_{otp}', email, timeout=600)

        send_mail(
            subject="Your OTP for Password Reset",
            message=f"Your OTP is {otp}. It is valid for 10 minutes.",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
        )

        return Response({'message': 'OTP sent to your email.'}, status=200)

    
class Verify(APIView):
    def post(self, request):
        otp = request.data.get('otp')
        email = cache.get(f'email_for_otp_{otp}')

        if not email:
            return Response({'error': 'OTP expired or invalid.'}, status=400)

        real_otp = cache.get(f'otp_{email}')
        if real_otp != otp:
            return Response({'error': 'Incorrect OTP.'}, status=400)

       
        cache.delete(f'otp_{email}')
        cache.delete(f'email_for_otp_{otp}')

       
        return Response({'message': 'OTP verified successfully.', 'email': email})


from django.contrib.auth.hashers import make_password
class ResetPassword(APIView):
    def post(self, request):
        email = request.data.get('email')  
        password = request.data.get('new_password')

        if not email or not password:
            return Response({'error': 'Missing email or password.'}, status=400)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'error': 'User not found.'}, status=404)

        user.password = make_password(password)
        user.save()

        return Response({'message': 'Password reset successful.'})


# views.py
class ChangePassword(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Password changed'})
        return Response(serializer.errors, status=400)


class GoogleLoginView(APIView):
    def post(self, request):
        id_token_from_client = request.data.get("id_token")
        if not id_token_from_client:
            return Response({"error": "No id_token provided"}, status=400)

        try:
            # Replace with your actual client ID
            CLIENT_ID = "440923686502-ntt2cvss5dcaobolfsetp2q3dkf2jmd9.apps.googleusercontent.com"
            idinfo = id_token.verify_oauth2_token(
                id_token_from_client,
                Request(),
                CLIENT_ID
            )

            email = idinfo.get("email")
            if not email:
                return Response({"error": "Email not found in token"}, status=400)

            # Find or create the user
            user = User.objects.filter(email=email).first()
            if not user:
                username = email.split("@")[0]
                user = User.objects.create(
                    username=username,
                    email=email
                )
                user.set_unusable_password()
                user.save()

            refresh = RefreshToken.for_user(user)

            return Response({
                "tokens": {
                    "access": str(refresh.access_token),
                    "refresh": str(refresh)
                },
                "user": {
                    "username": user.username,
                    "email": user.email
                }
            })

        except ValueError as ve:
            print("Google Token Error:", ve)
            return Response({"error": f"Invalid token: {str(ve)}"}, status=400)

        except Exception as e:
            print("Unexpected Error:", e)
            return Response({"error": f"Server error: {str(e)}"}, status=500)

import os
import requests
  

from rest_framework.views import APIView
from rest_framework.response import Response
import os
import requests
import re

class ResumeExtracter(APIView):
    permission_classes = [IsAuthenticated] 
    def post(self, request):
        file = request.FILES.get('resume')
        description = request.data.get('description')

        if not file:
            return Response({"error": "No file uploaded."}, status=400)

        filename = file.name.lower()

        try:
            # Extract resume text and URLs
            if filename.endswith(".pdf"):
                text = extract_text_from_pdf(file)
            elif filename.endswith(".docx"):
                text = extract_text_from_docx(file)
            else:
                return Response({"error": "Unsupported file type."}, status=400)

            github_url = extract_github_url(text)
            linkedin_url = extract_linkedin_url(text)
            github_data = fetch_full_github_data(github_url) if github_url else None

            headers = {
                "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
            }

            prompt = f"""
            You are an expert resume reviewer.

            At the top of your response, start with:
            **Match Score: XX** (replace XX with a number from 0 to 100)

            Then continue with your analysis:

             Missing Keywords
            (List technical/skill-based keywords from JD that are missing or weak)

             Suggestions to Improve
            (Give detailed, actionable suggestions to improve resume, GitHub, or alignment)

             ATS-Friendliness Feedback
            (Check for formatting, keywords, readability for ATS tools)

             GitHub Review
            (Analyze each project, code quality, relevance, readme, etc.)

             LinkedIn Suggestions
            (Evaluate headline, about, experience, and projects)

            ---

            Resume:
            {text}

            Job Description:
            {description}

            GitHub Info:
            {github_data}

            LinkedIn URL:
            {linkedin_url}
            """

            payload = {
                "model": "mistralai/mistral-7b-instruct",
                "messages": [{"role": "user", "content": prompt}]
            }

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            full_content = result.get("choices", [{}])[0].get("message", {}).get("content")

            if full_content:
                # Extract match score
                score_match = re.search(r"\*\*Match Score:\s*(\d+)\*\*", full_content)
                score_value = int(score_match.group(1)) if score_match else None

                # Remove score from analysis if present
                analysis_text = re.sub(r"\*\*Match Score:\s*\d+\*\*", "", full_content).strip()

                return Response({
                    "score": score_value,
                    "analysis": analysis_text
                }, status=200)
            else:
                return Response({"error": "No analysis received."}, status=500)

        except requests.RequestException as e:
            return Response({"error": f"Request failed: {str(e)}"}, status=500)
        except Exception as e:
            return Response({"error": f"Internal server error: {str(e)}"}, status=500)


import os

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("models/gemini-2.5-flash")
class gemini_chat(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):
        content=request.data.get('message')
        if not content:
            return Response({"error": "Message is required"}, status=status.HTTP_400_BAD_REQUEST)
        messages = ChatMessage.objects.filter(user=request.user)
        counter=0
        history=[]

        for i in messages:
            history.append({'role': i.role, 'parts': [i.content]})
            counter=counter+1
        try:
            chat = model.start_chat(history=history)
            response = chat.send_message(content)

            # Save both user message and Gemini response
            ChatMessage.objects.create(user=request.user, role="user", content=content)
            ChatMessage.objects.create(user=request.user, role="model", content=response.text)
            return Response({"reply": response.text})
        except  Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

class ProfileUpdate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data, status=200)

    def patch(self, request):
        serializer = ProfileSerializer(request.user, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response({
                'message': 'Validation failed',
                'errors': serializer.errors
            }, status=400)

        serializer.save()
        return Response({
            'message': 'Profile updated successfully',
            'data': serializer.data
        }, status=200)

    
from django.http import HttpResponse
import logging

logger = logging.getLogger(__name__)

def home(request):
    logger.info("Home endpoint was called")
    return HttpResponse("🚀 Deployed successfully!", status=200)

def health_check(request):
    return HttpResponse("OK", status=200)


# views.py
from django.contrib.auth import get_user_model
from django.http import HttpResponse

def create_admin(request):
    User = get_user_model()
    try:
        if not User.objects.filter(username="A.C.Nithin").exists():
            User.objects.create_superuser(
                username="A.C.Nithin",
                email="pavan@gmail.com",
                password="Pavan@1428#"
            )
            return HttpResponse("Superuser created.")
        return HttpResponse("Superuser already exists.")
    except Exception as e:
        return HttpResponse(f"Error: {e}", status=500)

