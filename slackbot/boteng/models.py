from djongo import models


class Event(models.Model):
    summary = models.CharField(max_length=120)
    creator = models.CharField(max_length=50)
    start_date = models.DateTimeField(auto_now_add=False, auto_now=False)
    end_date = models.DateTimeField(auto_now_add=False, auto_now=False)

    def __str__(self):
        return self.summary


class CalendarUsers(models.Model):
    email = models.CharField(max_length=120)
    role = models.CharField(max_length=20)
