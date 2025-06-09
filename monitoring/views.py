from django.shortcuts import render, redirect
import csv
from .forms import UploadCSVForm
from .models import EmployeeOvertime
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import urllib, base64

def dashboard(request):
    return render(request, 'monitoring/dashboard.html')

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

def show_overtime_records(request):
    records = EmployeeOvertime.objects.all().order_by('-date')  # recent first
    return render(request, 'monitoring/employee_overtime_list.html', {'records': records})

def overtime_analysis(request):
    # Step 1: Load data from DB
    queryset = EmployeeOvertime.objects.all().values()
    df = pd.DataFrame(queryset)

    if df.empty:
        return render(request, 'analysis/analysis_dashboard.html', {'message': 'No data available.'})

    # Step 2: Convert date to datetime
    df['date'] = pd.to_datetime(df['date'])

    # --- ANALYSIS ---

    # 1. Total Overtime by Employee
    overtime_summary = df.groupby(['name', 'department'])['overtime_hours'].sum().reset_index()

    # 2. Total overtime by department
    department_overtime = df.groupby('department')['overtime_hours'].sum().reset_index()

    # 3. High Overtime Employees
    high_overtime = overtime_summary[overtime_summary['overtime_hours'] > 4]

    # 4. Monthly Trends
    df['month'] = df['date'].dt.to_period('M')
    monthly_trends = df.groupby(['month', 'department'])['overtime_hours'].sum().reset_index()

    # 5. Overtime by Day of Week
    df['day_of_week'] = df['date'].dt.day_name()
    weekday_overtime = df.groupby('day_of_week')['overtime_hours'].sum().reset_index()

    # 6. Consistent High Overtime (no performance data yet)
    employee_stats = df.groupby('name')['overtime_hours'].agg(['mean', 'std']).reset_index()
    consistent_high = employee_stats[(employee_stats['mean'] > 40) & (employee_stats['std'] < 5)]

    context = {
        'overtime_summary': overtime_summary.to_dict(orient='records'),
        'department_overtime': department_overtime.to_dict(orient='records'),
        'high_overtime': high_overtime.to_dict(orient='records'),
        'monthly_trends': monthly_trends.to_dict(orient='records'),
        'weekday_overtime': weekday_overtime.to_dict(orient='records'),
        'consistent_high': consistent_high.to_dict(orient='records'),
    }

    return render(request, 'analysis/analysis_dashboard.html', context)

def visual_analysis(request):
    queryset = EmployeeOvertime.objects.all().values()
    df = pd.DataFrame(queryset)

    # 1. Total Overtime by Employee
    # Plotting
    overtime_summary = df.groupby(['name', 'department'])['overtime_hours'].sum().reset_index()
    plt.figure(figsize=(12, 6))
    plt.bar(overtime_summary['name'], overtime_summary['overtime_hours'], color='skyblue', width=0.3)
    plt.xlabel('Employee Name')
    plt.ylabel('Total Overtime Hours')
    plt.xticks(rotation=0, ha='right')
    plt.tight_layout()

    # Save to buffer
    buf1 = io.BytesIO()
    plt.savefig(buf1, format='png')
    buf1.seek(0)
    image_base64 = base64.b64encode(buf1.read()).decode('utf-8')
    buf1.close()
    plt.close()

    # 2. Total Overtime by Department
    department_overtime = df.groupby('department')['overtime_hours'].sum().reset_index()
    plt.figure(figsize=(12,6))
    plt.bar(department_overtime['department'], department_overtime['overtime_hours'], color='skyblue', width=0.3)
    plt.xlabel('Department')
    plt.ylabel('Total Overtime Hours')
    plt.xticks(rotation=0, ha='right')
    plt.tight_layout()

    #Save to Buffer
    buf2 = io.BytesIO()
    plt.savefig(buf2, format='png')
    buf2.seek(0)
    image2_base64 = base64.b64encode(buf2.read()).decode('utf-8')
    buf2.close()
    plt.close()

    x = {
        'emp_overtime_chart': image_base64,
        'dep_overtime_chart': image2_base64,
    }

    return render(request, 'analysis/diagrams.html', x)