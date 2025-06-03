from django.shortcuts import render, redirect
import csv
from .forms import UploadCSVForm
from .models import EmployeeOvertime

def dashboard(request):
    return render(request, 'monitoring\dashboard.html')


def upload_csv(request):
    if request.method == 'POST':
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['file']
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            for row in reader:
                EmployeeOvertime.objects.create(
                    employee_id=row['employee_id'],
                    name=row['name'],
                    department=row['department'],
                    date=row['date'],
                    hours_worked=float(row['hours_worked']),
                    regular_hours=float(row['regular_hours']),
                    overtime_hours=float(row['overtime_hours']),
                )
            return redirect('dashboard')
    else:
        form = UploadCSVForm()
    return render(request, 'monitoring/upload.html', {'form': form})