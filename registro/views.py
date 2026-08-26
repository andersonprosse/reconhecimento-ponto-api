import cv2
import os
import numpy as np
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
from django.core.files.base import ContentFile
from .models import Funcionario, ColetaFaces, Treinamento
from .serializers import FuncionarioSerializer

class FuncionarioViewSet(viewsets.ModelViewSet):
    queryset = Funcionario.objects.all()
    serializer_class = FuncionarioSerializer

# Inicializa o classificador (usamos path absoluto ou o arquivo xml na raiz)
face_cascade = cv2.CascadeClassifier(os.path.join(settings.BASE_DIR, 'haarcascade_frontalface_default.xml'))

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_face_treinamento(request, funcionario_id):
    """
    Endpoint para receber uma imagem via POST (multipart form data),
    detectar o rosto e salvar na tabela ColetaFaces para aquele funcionário.
    """
    try:
        funcionario = Funcionario.objects.get(id=funcionario_id)
    except Funcionario.DoesNotExist:
        return Response({'erro': 'Funcionário não encontrado'}, status=status.HTTP_404_NOT_FOUND)

    file_obj = request.FILES.get('image')
    if not file_obj:
        return Response({'erro': 'Nenhuma imagem enviada'}, status=status.HTTP_400_BAD_REQUEST)

    # Verifica quantas imagens o funcionario já tem
    if ColetaFaces.objects.filter(funcionario=funcionario).count() >= 10:
        return Response({'erro': 'Limite de 10 amostras atingido para este funcionário.'}, status=status.HTTP_400_BAD_REQUEST)

    # Lê a imagem em memória e converte para formato do OpenCV
    file_bytes = np.asarray(bytearray(file_obj.read()), dtype=np.uint8)
    frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    if frame is None:
        return Response({'erro': 'Arquivo de imagem inválido'}, status=status.HTTP_400_BAD_REQUEST)

    # Processamento e detecção de rosto
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    if len(faces) == 0:
        return Response({'erro': 'Nenhum rosto detectado na imagem.'}, status=status.HTTP_400_BAD_REQUEST)

    if len(faces) > 1:
        return Response({'erro': 'Mais de um rosto detectado. Envie foto com apenas uma pessoa.'}, status=status.HTTP_400_BAD_REQUEST)

    # Pega o primeiro rosto
    (x, y, w, h) = faces[0]
    cropped_face = frame[y:y+h, x:x+w]
    
    largura, altura = 220, 220
    face_resized = cv2.resize(cropped_face, (largura, altura))
    face_gray = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)

    # Codifica a imagem processada diretamente na memória RAM (sem salvar no HD)
    ret, buffer = cv2.imencode('.jpg', face_gray)
    if not ret:
        return Response({'erro': 'Falha ao processar a imagem internamente.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    # Cria a instância no banco de dados
    coleta = ColetaFaces.objects.create(funcionario=funcionario)
    
    # Converte o buffer da memória para o formato de Arquivo do Django e salva diretamente na base/cloud
    image_file = ContentFile(buffer.tobytes(), name=f"{funcionario.slug}_{coleta.id}.jpg")
    coleta.image.save(image_file.name, image_file)

    return Response({
        'mensagem': 'Rosto detectado e salvo com sucesso.',
        'coletas_salvas': ColetaFaces.objects.filter(funcionario=funcionario).count()
    })

@api_view(['POST'])
def treinar_modelo(request):
    """
    Endpoint para iniciar o treinamento da IA com as fotos salvas em ColetaFaces.
    """
    coletas = ColetaFaces.objects.all()
    if not coletas:
        return Response({'erro': 'Nenhuma face coletada para treinamento.'}, status=status.HTTP_400_BAD_REQUEST)

    faces = []
    ids = []
    
    for coleta in coletas:
        try:
            path = coleta.image.path
            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if img is not None:
                faces.append(img)
                ids.append(coleta.funcionario.id)
        except Exception as e:
            continue
            
    if not faces:
        return Response({'erro': 'Falha ao processar imagens para treinamento.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    recognizer = cv2.face.LBPHFaceRecognizer_create(radius=2, neighbors=12, grid_x=8, grid_y=8)
    recognizer.train(faces, np.array(ids))
    
    treinamento_dir = os.path.join(settings.MEDIA_ROOT, 'treinamento')
    if not os.path.exists(treinamento_dir):
        os.makedirs(treinamento_dir)
        
    model_path = os.path.join(treinamento_dir, 'classificadorEigen.yml')
    recognizer.write(model_path)
    
    # Salva no banco de dados (apenas um)
    Treinamento.objects.all().delete()
    treinamento = Treinamento()
    treinamento.modelo.name = 'treinamento/classificadorEigen.yml'
    treinamento.save()

    return Response({'mensagem': 'Treinamento realizado com sucesso.'})

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def bater_ponto_reconhecimento(request):
    """
    Endpoint que recebe a imagem do rosto no momento de bater o ponto
    e faz o reconhecimento.
    """
    file_obj = request.FILES.get('image')
    if not file_obj:
        return Response({'erro': 'Nenhuma imagem enviada.'}, status=status.HTTP_400_BAD_REQUEST)

    treinamento = Treinamento.objects.first()
    if not treinamento:
        return Response({'erro': 'Modelo de IA não treinado.'}, status=status.HTTP_400_BAD_REQUEST)

    model_path = os.path.join(settings.MEDIA_ROOT, treinamento.modelo.name)
    if not os.path.exists(model_path):
        return Response({'erro': 'Arquivo de modelo não encontrado.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    recognizer = cv2.face.LBPHFaceRecognizer_create(radius=2, neighbors=12, grid_x=8, grid_y=8)
    recognizer.read(model_path)

    file_bytes = np.asarray(bytearray(file_obj.read()), dtype=np.uint8)
    frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    
    if frame is None:
        return Response({'erro': 'Arquivo de imagem inválido'}, status=status.HTTP_400_BAD_REQUEST)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    if len(faces) == 0:
        return Response({'erro': 'Rosto não detectado.'}, status=status.HTTP_400_BAD_REQUEST)
    
    if len(faces) > 1:
        return Response({'erro': 'Mais de uma pessoa detectada. Mantenha apenas uma pessoa na câmera.'}, status=status.HTTP_400_BAD_REQUEST)

    (x, y, w, h) = faces[0]
    cropped_face = gray[y:y+h, x:x+w]
    face_resized = cv2.resize(cropped_face, (220, 220))

    # Realiza predição
    id_previsto, confianca = recognizer.predict(face_resized)
    
    # Aqui voce pode ajustar a confianca. LBPH, qto menor, melhor a distancia. 
    # Em geral > 60 ja comeca a errar muito
    if confianca > 85:
        return Response({'erro': 'Rosto desconhecido ou confiança baixa.', 'confianca_gerada': confianca}, status=status.HTTP_401_UNAUTHORIZED)

    try:
        funcionario = Funcionario.objects.get(id=id_previsto)
    except Funcionario.DoesNotExist:
        return Response({'erro': 'Funcionário identificado não existe no banco.'}, status=status.HTTP_404_NOT_FOUND)

    # TODO: Inserir logica para salvar na tabela registros_ponto (Fase 2 db)
    
    return Response({
        'mensagem': f'Ponto registrado para {funcionario.nome}',
        'funcionario_id': funcionario.id,
        'nome': funcionario.nome,
        'confianca': confianca
    })
