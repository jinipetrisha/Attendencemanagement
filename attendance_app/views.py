import base64
import qrcode
import numpy as np
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .models import Student,Attendance
from PIL import Image
import io
from django.contrib import messages
import torch
from datetime import datetime, date
from django.db.models import Q,Count
from io import BytesIO
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

def view_attendance(request):
    class_id = request.GET.get('class_id', '')
    subject = request.GET.get('subject', '')
    date = request.GET.get('date', '')
    attendances = Attendance.objects.all()
    if class_id:
        attendances = attendances.filter(class_id__icontains=class_id)
    if subject:
        attendances = attendances.filter(subject__icontains=subject)
    if date:
        attendances = attendances.filter(date=date)
    return render(request, 'view_attendance.html', {
        'attendances': attendances,
        'class_id': class_id,
        'subject': subject,
        'date': date,
    })
def attendance_summary(request):
    sections = Student.objects.values_list('section', flat=True).distinct()
    summary = []
    for section in sections:
        students = Student.objects.filter(section=section)
        present_today = Attendance.objects.filter(date=date.today(), student__in=students)
        present_ids = present_today.values_list('student_id', flat=True)
        present = students.filter(id__in=present_ids)
        absent = students.exclude(id__in=present_ids)
        summary.append({
            'section': section,
            'present': present,
            'absent': absent,
            'total': students.count()
        })
    return render(request, 'attendance_summary.html', {'summary': summary})
from django.shortcuts import render

def home(request):
    return render(request, 'home.html')
def scan_qr_and_attend(request):
    if request.method == 'POST':
        qr_data = request.POST.get("qr_data")
        image_data = request.POST.get("image_data")

        # ✅ Validate QR data
        try:
            class_id, subject, scan_date = qr_data.split("|")
            if scan_date != str(date.today()):
                messages.error(request, "QR code is not valid for today.")
                return redirect("scan_qr")
        except:
            messages.error(request, "Invalid QR code format.")
            return redirect("scan_qr")

        # Decode image from base64
        format, imgstr = image_data.split(';base64,') 
        image = Image.open(io.BytesIO(base64.b64decode(imgstr)))

        # Get face embedding
        face = mtcnn(image)
        if face is None:
            return render(request, 'scan_qr.html', {'error': "No face detected."})

        with torch.no_grad():
            input_embedding = resnet(face.unsqueeze(0)).detach().numpy()

        # Compare with registered embeddings
        students = Student.objects.all()
        matched_student = None
        for student in students:
            db_embedding = student.get_face_encoding()
            distance = np.linalg.norm(input_embedding - db_embedding)
            if distance < 0.8:  # Tweak threshold as needed
                matched_student = student
                break

        if matched_student:
            # Check if already marked
            already_marked = Attendance.objects.filter(
                student=matched_student, class_id=class_id, subject=subject, date=scan_date
            ).exists()
            if already_marked:
                return render(request, 'scan_qr.html', {'info': "Attendance already marked."})

            # Save attendance
            Attendance.objects.create(
                student=matched_student,
                class_id=class_id,
                subject=subject,
                date=scan_date,
                time=datetime.now().time()
            )
            return render(request, 'scan_qr.html', {'success': matched_student.name})
        else:
            return render(request, 'scan_qr.html', {'error': "Face not recognized."})

    return render(request, 'scan_qr.html')


from facenet_pytorch import MTCNN, InceptionResnetV1

# Initialize models
mtcnn = MTCNN(image_size=160, margin=0)
resnet = InceptionResnetV1(pretrained='vggface2').eval()
def generate_qr(request):
    if request.method == 'POST':
        class_id = request.POST['class_id']          # ⬅️ Form input from teacher
        subject = request.POST['subject']
        today = str(date.today())                    # ⬅️ Ensure QR is tied to today's date
        qr_data = f"{class_id}|{subject}|{today}"    # ⬅️ Format: e.g., "10A|Math|2025-05-22"

        # 🔁 Generate QR code
        qr = qrcode.make(qr_data)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        qr_image_base64 = base64.b64encode(buffer.getvalue()).decode()  # ⬅️ Encode to base64 for <img> tag

        # ✅ Send to template for display
        return render(request, 'generate_qr.html', {
            'qr_data': qr_data,
            'qr_image': qr_image_base64,
        })

    # 🟦 GET request: show the empty form
    return render(request, 'generate_qr.html')

from django.contrib import messages  # Add this at the top

def register_student(request):
    if request.method == 'POST':
        name = request.POST['name']
        student_id = request.POST['student_id']
        image_data = request.POST['image_data']

        # ✅ Check for duplicates before processing
        if Student.objects.filter(student_id=student_id).exists():
            messages.warning(request, "Student ID already registered.")
            return render(request, 'register.html', {'already_registered': True})

        if Student.objects.filter(name=name).exists():
            messages.warning(request, "Student name already registered.")
            return render(request, 'register.html')

        # Decode base64 image
        format, imgstr = image_data.split(';base64,') 
        image = Image.open(io.BytesIO(base64.b64decode(imgstr)))

        # Detect face and get embedding
        face = mtcnn(image)
        if face is not None:
            with torch.no_grad():
                embedding = resnet(face.unsqueeze(0)).detach().numpy()

            # Save student
            student = Student(name=name, student_id=student_id)
            student.save_face_encoding(embedding[0])
            student.save()

            messages.success(request, "Student registered successfully.")
            return render(request, 'register.html', {'success': True})
        else:
            messages.error(request, "No face detected.")
            return render(request, 'register.html', {'error': "No face detected."})

    return render(request, 'register.html')
def student_dashboard(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    
    total_days = Attendance.objects.values('date').distinct().count()
    present_days = Attendance.objects.filter(student=student).values('date').distinct().count()
    attended_today = Attendance.objects.filter(student=student, date=date.today()).exists()
    
    percent = (present_days / total_days * 100) if total_days > 0 else 0

    return render(request, 'student_dashboard.html', {
        'student': student,
        'attended_today': attended_today,
        'present_days': present_days,
        'total_days': total_days,
        'percent': round(percent, 2),
    })

def teacher_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:  # Teacher check
            login(request, user)
            return redirect('teacher_dashboard')
        else:
            return render(request, 'teacher_login.html', {
                'error': 'Invalid credentials or not authorized.'
            })

    return render(request, 'teacher_login.html')


@login_required
def teacher_dashboard(request):
    return render(request, 'generate_qr.html')
