from django.http import JsonResponse
import os,sys

def health( request ):
  return JsonResponse(  {  "ok":True,"who":"last save wins" } )
