from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ObligationViewSet, NettingWindowViewSet, ParticipantBalanceViewSet


router = DefaultRouter()
router.register(r'obligations', ObligationViewSet)
router.register(r'netting-windows', NettingWindowViewSet)
router.register(r'balances', ParticipantBalanceViewSet)

urlpatterns = [
    path('', include(router.urls)),
]