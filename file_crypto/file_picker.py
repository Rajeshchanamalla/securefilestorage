from django.shortcuts import render
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage

def file_upload_view(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        fs = FileSystemStorage()
        file_path = fs.save(uploaded_file.name, uploaded_file)
        file_url = fs.url(file_path)
        return JsonResponse({'file_url': file_url})
    return render(request, 'file_upload.html')
