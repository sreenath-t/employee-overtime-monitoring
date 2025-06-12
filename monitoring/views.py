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
    max_value = overtime_summary['overtime_hours'].max()
    high_overtime_emp = overtime_summary[overtime_summary['overtime_hours'] == max_value]

    # 4. High Overtime Dep
    department_overtime = df.groupby('department')['overtime_hours'].sum().reset_index()
             #   Find the maximum overtime value
    max_overtime = department_overtime['overtime_hours'].max()
             #   Filter teams with that maximum value
    high_overtime_dep = department_overtime[department_overtime['overtime_hours'] == max_overtime]


    # 5. Monthly Trends
    df['month'] = df['date'].dt.to_period('M')
    monthly_trends = df.groupby(['month', 'department'])['overtime_hours'].sum().reset_index()

    # 6. Overtime by Day of Week
    df['day_of_week'] = df['date'].dt.day_name()
    weekday_overtime = df.groupby('day_of_week')['overtime_hours'].sum().reset_index()

    # 7. Consistent High Overtime
    #employee_stats = df.groupby('name')['overtime_hours'].agg(['mean', 'std']).reset_index()
    #consistent_high = employee_stats[(employee_stats['mean'] > 40) & (employee_stats['std'] < 5)]

    # 1. Set a threshold for "high overtime" per day
    THRESHOLD = 1  # e.g., >2 hours considered high
    MIN_PERCENT_DAYS = 0.65  # 70% of working days

    # 2. Count total days and high overtime days per employee
    df['high_overtime_flag'] = df['overtime_hours'] > THRESHOLD

    total_days = df.groupby('name')['date'].nunique().reset_index(name='total_days')
    high_overtime_days = df[df['high_overtime_flag']].groupby('name')['date'].nunique().reset_index(name='high_days')

    # 3. Merge and calculate ratio
    merged = pd.merge(total_days, high_overtime_days, on='name', how='left').fillna(0)
    merged['high_ratio'] = merged['high_days'] / merged['total_days']

    #  4. Filter consistent high overtime employees
    consistent_high = merged[merged['high_ratio'] >= MIN_PERCENT_DAYS]

    # 5. Add employee metadata
    employee_info = df[['name', 'employee_id', 'department']].drop_duplicates()
    consistent_high = pd.merge(consistent_high, employee_info, on='name', how='left')


    context = {
        'overtime_summary': overtime_summary.to_dict(orient='records'),
        'department_overtime': department_overtime.to_dict(orient='records'),
        'high_overtime_emp': high_overtime_emp.to_dict(orient='records'),
        'high_overtime_dep': high_overtime_dep.to_dict(orient='records'),
        'monthly_trends': monthly_trends.to_dict(orient='records'),
        'weekday_overtime': weekday_overtime.to_dict(orient='records'),
        'consistent_high': consistent_high.to_dict(orient='records'),
    }

    return render(request, 'analysis/analysis_dashboard.html', context)

def visual_analysis(request):
    queryset = EmployeeOvertime.objects.all().values()
    df = pd.DataFrame(queryset)

    df['date'] = pd.to_datetime(df['date'])

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

    # 3. Monthly Overtime Trends
    df['month'] = df['date'].dt.to_period('M')
    monthly_trends = df.groupby(['month', 'department'])['overtime_hours'].sum().reset_index()
    monthly_trends['dept_month'] = monthly_trends['department'].astype(str) + ' -> ' + monthly_trends['month'].astype(str)
    plt.figure(figsize=(12,6))
    plt.bar(monthly_trends['dept_month'], monthly_trends['overtime_hours'], color='skyblue', width=0.3)
    plt.xlabel('Department')
    plt.ylabel('Total Overtime Hours')
    plt.xticks(rotation=0, ha='right')
    plt.tight_layout()

    #Save to Buffer
    buf3 = io.BytesIO()
    plt.savefig(buf3, format='png')
    buf3.seek(0)
    image3_base64 = base64.b64encode(buf3.read()).decode('utf-8')
    buf3.close()
    plt.close()

    # 4. Overtime by Day of Week
    df['day_of_week'] = df['date'].dt.day_name()
    weekday_overtime = df.groupby('day_of_week')['overtime_hours'].sum().reset_index()
    plt.figure(figsize=(12,6))
    plt.bar(weekday_overtime['day_of_week'], weekday_overtime['overtime_hours'], color='skyblue', width=0.3)
    plt.xlabel('Day of Week')
    plt.ylabel('Total Overtime Hours')
    plt.xticks(rotation=0, ha='right')
    plt.tight_layout()

    #Save to Buffer
    buf4 = io.BytesIO()
    plt.savefig(buf4, format='png')
    buf4.seek(0)
    image4_base64 = base64.b64encode(buf4.read()).decode('utf-8')
    buf4.close()
    plt.close()

    # 5. Individual Employee Analysis
    THRESHOLD = 1  # e.g., >2 hours considered high
    MIN_PERCENT_DAYS = 0.65  # 70% of working days

    df['high_overtime_flag'] = df['overtime_hours'] > THRESHOLD

    total_days = df.groupby('name')['date'].nunique().reset_index(name='total_days')
    high_overtime_days = df[df['high_overtime_flag']].groupby('name')['date'].nunique().reset_index(name='high_days')

    merged = pd.merge(total_days, high_overtime_days, on='name', how='left').fillna(0)
    merged['high_ratio'] = merged['high_days'] / merged['total_days']

    consistent_high = merged[merged['high_ratio'] >= MIN_PERCENT_DAYS]

    employee_info = df[['name', 'employee_id', 'department']].drop_duplicates()
    consistent_high = pd.merge(consistent_high, employee_info, on='name', how='left')
    plt.figure(figsize=(12,6))
    plt.bar(consistent_high['name'], consistent_high['high_ratio'], color='coral', width=0.3)
    plt.xlabel('Employee')
    plt.ylabel('Total Overtime Hours')
    plt.xticks(rotation=0, ha='right')
    plt.tight_layout()

    #Save to Buffer
    buf5 = io.BytesIO()
    plt.savefig(buf5, format='png')
    buf5.seek(0)
    image5_base64 = base64.b64encode(buf5.read()).decode('utf-8')
    buf5.close()
    plt.close()

    x = {
        'emp_overtime_chart': image_base64,
        'dep_overtime_chart': image2_base64,
        'monthly_overtime_trends': image3_base64,
        'overtime_by_day_of_week': image4_base64,
        'individual_emp_analysis': image5_base64
    }

    return render(request, 'analysis/diagrams.html', x)