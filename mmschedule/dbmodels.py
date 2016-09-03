from django.db import models

class Session(models.Model):
	id = models.BigIntegerField(primary_key=True, unique=True)
	data = models.CharField(max_length=50)
	
class Pref(models.Model):
	id = models.BigIntegerField(primary_key=True, unique=True)
	type = models.CharField(max_length=1)
	gt_as_string = models.CharField(max_length=80)
	gt_id = models.PositiveSmallIntegerField()