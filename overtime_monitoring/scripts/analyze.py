import pandas as pd
import matplotlib.pyplot as plt
from monitoring.models import EmployeeOvertime

def load_data():
    qs = EmployeeOvertime.objects.all().values()
    df = pd.DataFrame.from_records(qs)
    return df

def analyze_overtime(df):
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.to_period('M')

    # Total Overtime by Department
    dept_overtime = df.groupby('department')['overtime_hours'].sum()
    dept_overtime.plot(kind='bar', title='Total Overtime by Department')
    plt.tight_layout()
    plt.savefig('static/department_overtime.png')
    plt.clf()
