import json
import logging
import base64
import time
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.files.storage import FileSystemStorage
import base64
import time
import os
from io import BytesIO
from django.conf import settings

from django.contrib.auth.models import User
from asgiref.sync import sync_to_async
from django.core.files.base import ContentFile
import uuid
from channels.db import database_sync_to_async
import logging
import asyncio
from django.utils import timezone
from channels.generic.websocket import AsyncWebsocketConsumer
import requests
from .chatmodel import get_gemini_response

logger = logging.getLogger(__name__)


class chatsystem(AsyncWebsocketConsumer):

	fs = FileSystemStorage()

	async def connect(self):

		#check if user is authenticated
		# if self.scope["user"].is_anonymous:
		# 	await self.close()
		# 	return
		
		await self.accept()


	async def receive(self, text_data=None, bytes_data=None):
		# Handle incoming text messages (prioritize text_data)
		packet = json.loads(text_data)

		#check if request contain a image file	
		# if packet['isImage']:
			
		# 	image_data = base64.b64decode(packet['message'].split(',')[1])
		# 	filename = f"image_{int(time.time())}_{uuid.uuid4().hex[:8]}.png"
        #       # use ContentFile so Django handles file content correctly
		# 	file_path = self.fs.save(filename, ContentFile(image_data))
			
		# 	insight = requests.get(f"http://localhost:8000/plant?path={file_path}")

		# 	await self.send(text_data=json.dumps({
		# 		"type": "connection_established",
		# 		"message": insight.json()
		# 	}))
			
		user_prompt = packet['message']
		full_response_content = ""
		async for token in get_gemini_response(user_prompt):
			full_response_content += token
			await self.send(text_data=json.dumps({
                'type': 'token',
                'content': token
            }))

		await self.send(text_data=json.dumps({
                'type': 'cmd',
                'content': "END"
            }))


		

	async def disconnect(self, close_code):
		# Optional: perform cleanup here
		logger.debug("WebSocket disconnected (code=%s)", close_code)

