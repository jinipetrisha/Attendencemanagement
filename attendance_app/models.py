from django.db import models
import numpy as np
import base64

class Student(models.Model):
    name = models.CharField(max_length=100)
    student_id = models.CharField(max_length=50, unique=True)
    face_encoding = models.BinaryField()

    def __str__(self):
        return f"{self.name} ({self.student_id})"

    def save_face_encoding(self, encoding):
        self.face_encoding = base64.b64encode(encoding.tobytes())

    def get_face_encoding(self):
        return np.frombuffer(base64.b64decode(self.face_encoding), dtype=np.float32)


class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    class_id = models.CharField(max_length=50)
    subject = models.CharField(max_length=100)
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.name} - {self.subject} on {self.date}"
