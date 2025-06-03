from django.db import models

class EmployeeOvertime(models.Model):
    employee_id = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    date = models.DateField()
    hours_worked = models.FloatField()
    regular_hours = models.FloatField(default=8.0)
    overtime_hours = models.FloatField()

    def __str__(self):
        return f"{self.name} ({self.date})"
