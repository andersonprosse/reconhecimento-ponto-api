from rest_framework import serializers
from .models import Funcionario, ColetaFaces, Treinamento

class FuncionarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Funcionario
        fields = '__all__'
        # Avisa que foto e slug não são obrigatórios no cadastro inicial
        extra_kwargs = {
            'foto': {'required': False},
            'slug': {'required': False}
        }

class ColetaFacesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ColetaFaces
        fields = '__all__'

class TreinamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Treinamento
        fields = '__all__'
