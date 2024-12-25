import json
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django_elasticsearch_dsl.search import Search  # 导入 Search 类
from users.models import User
# Create your views here.

from django.http import HttpResponse, JsonResponse
from papers.models import Paper
from comments.models import Comment
from django.utils import timezone
import json

# Create your views here.

def send_information(request):
    if(request.method=='GET'):
        try:
            body = json.loads(request.body)
            fromUserId = body['fromUserId']
            toUserId=body['toUserId']
            content=body['content']

            sender=User.objects.get(user_id=fromUserId)
            receiver=User.objects.get(user_id=toUserId)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
