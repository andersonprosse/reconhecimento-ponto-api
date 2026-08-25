from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FuncionarioViewSet, upload_face_treinamento, treinar_modelo, bater_ponto_reconhecimento

router = DefaultRouter()
router.register(r'funcionarios', FuncionarioViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/treinamento/upload/<int:funcionario_id>/', upload_face_treinamento, name='upload_face_treinamento'),
    path('api/treinamento/iniciar/', treinar_modelo, name='treinar_modelo'),
    path('api/ponto/bater/', bater_ponto_reconhecimento, name='bater_ponto_reconhecimento'),
]