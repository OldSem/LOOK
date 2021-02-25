from rest_framework import generics
from .serializers import UserDetailsSerializer
from .models import User


class UsersList(generics.ListAPIView):
    serializer_class = UserDetailsSerializer

    def get_queryset(self):
        """
        This view should return a list of all the purchases
        for the currently authenticated user.
        """
        user = self.request.user
        if user.is_superuser:
        	return User.objects.all()

