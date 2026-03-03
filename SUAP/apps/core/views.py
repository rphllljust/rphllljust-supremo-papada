from django.shortcuts import render

def dashboard(request):
    return render(request, "core/dashboard.html")

def students_page(request):
    return render(request, "core/students.html")

def classes_page(request):
    return render(request, "core/classes.html")

def enrollments_page(request):
    return render(request, "core/enrollments.html")

def grades_page(request):
    return render(request, "core/grades.html")

def attendance_page(request):
    return render(request, "core/attendance.html")

def agenda_page(request):
    return render(request, "core/agenda.html")

def module_page(request, slug):
    return render(request, "core/module.html", {"slug": slug})