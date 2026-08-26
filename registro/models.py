from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from random import randint

class Funcionario(models.Model):
    slug = models.SlugField(max_length=200, unique=True)
    foto = models.ImageField(upload_to='foto/')
    nome = models.CharField(max_length=100)
    cpf = models.CharField(max_length=20)
    
    # Acesso
    usuario = models.CharField(max_length=50, unique=True, null=True, blank=True)
    senha = models.CharField(max_length=128, null=True, blank=True)
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.nome
    
    def save(self, *args, **kwargs):
        seq = self.nome + '_FUNC' + str(randint(1000000, 9999999))
        self.slug = slugify(seq)
        super().save(*args, **kwargs)


class ColetaFaces(models.Model):
    funcionario = models.ForeignKey(Funcionario, 
		    on_delete=models.CASCADE, related_name='funcionario_coletas')
    image = models.ImageField(upload_to='roi/')
    
    
class Treinamento(models.Model):
    modelo = models.FileField(upload_to='treinamento/') # .yml

    class Meta:
        verbose_name = 'Treinamento'
        verbose_name_plural = 'Treinamentos'

    def __str__(self):
        return 'Classificador (frontalface)'

    def clean(self):  # Limita a um único arquivo
        model = self.__class__
        if model.objects.exclude(id=self.id).exists():
            raise ValidationError('Só pode haver um arquivo salvo.')

class RegistroPonto(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada'),
        ('saida', 'Saída'),
        ('pausa_inicio', 'Início da Pausa'),
        ('pausa_fim', 'Fim da Pausa'),
    ]

    funcionario = models.ForeignKey(Funcionario, on_delete=models.CASCADE, related_name='registros_ponto')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='entrada')
    data_hora = models.DateTimeField(auto_now_add=True)
    foto_registro = models.ImageField(upload_to='ponto/', null=True, blank=True)
    confianca = models.FloatField(null=True, blank=True)

    class Meta:
        verbose_name = 'Registro de Ponto'
        verbose_name_plural = 'Registros de Ponto'

    def __str__(self):
        return f"{self.funcionario.nome} - {self.tipo} - {self.data_hora.strftime('%d/%m/%Y %H:%M')}"
