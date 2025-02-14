from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from django.shortcuts import get_object_or_404
from .models import Event, PromoCode
from .serializers import EventSerializer,PromoCodeSerializer

class EventListCreateView(APIView):
    def get(self, request):
        events = Event.objects.all()
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = EventSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
#to fetch all the events
class EventDetailView(APIView):
    def get(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        serializer = EventSerializer(event)
        return Response(serializer.data, status=status.HTTP_200_OK)


#to create promocodes
class PromoCodeListCreateView(generics.ListCreateAPIView):
    queryset = PromoCode.objects.all()
    serializer_class = PromoCodeSerializer

