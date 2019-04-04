from django.db import models
from django.contrib.auth.models import User
import uuid
from django.utils.crypto import get_random_string
from django.core.exceptions import ValidationError
import hashlib
from hashids import Hashids
hashids = Hashids()
from Auth.utils import FirebaseAPI

# Create your models here.
class Event(models.Model):
    name=models.CharField(max_length=20)
    min_members=models.PositiveIntegerField(default=1)
    max_members=models.PositiveIntegerField(default=1)
    is_registration_on=models.BooleanField(default=True)

    def create_team(self , user , t_name):

        team = Team.objects.create(event=self , creator = user,name=t_name)

        team.access_code = hashids.encode(team.id)
        team.save()

    def __str__(self):
        return self.name 

class EventDetail(models.Model):
    title=models.CharField(max_length=50)
    event=models.ForeignKey(Event,on_delete=models.CASCADE)
    content=models.TextField()
    priority=models.IntegerField()

    def __str__(self):
        return self.title + " for " + self.event.name 

class Institute(models.Model):
    name=models.CharField(max_length=200)
    is_active=models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Profile(models.Model):

    GENDER_CHOICES=(
        (0,'Male'),
        (1,'Female'),
        (2,'Others/Not Specified'),
    )
    INSTITUTE_TYPE_CHOICES=(
        (0,'Undergrad'),
        (1,'School'),
        (2,'Grad'),
        (3,'Professional'),
    )
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    referred_by=models.OneToOneField('Profile',null=True,related_name="referred",on_delete=models.DO_NOTHING)
    referral_code=models.UUIDField(default=uuid.uuid4)
    institute_name=models.ForeignKey(Institute,on_delete=models.SET_NULL,null=True) # can be school,college. leave blank for professionals 
    # year , if school, implies class, undergrad&masters == yearofpassing, professional==experience
    study_year=models.PositiveIntegerField(blank=True,null=True)
    # degree to be null for school
    degree=models.CharField(max_length=30,blank=True,null=True)
    # to be used only by undergrad and postgrad students
    branch=models.CharField(max_length=30,blank=True,null=True)
    country=models.CharField(max_length=40,null=True,blank=True)
    phone=models.CharField(max_length=15,blank=True)
    gender=models.IntegerField(null=True,choices=GENDER_CHOICES)
    resume=models.FileField(upload_to='media/resumes',null=True,blank=True)
    is_profile_complete=models.BooleanField(default=False)

    def __str__(self):
        return self.user.first_name + " from "+self.institute_name

    def get_or_set_profile_status(self, toSet=False):
        if toSet:
            self.is_profile_complete = True
            self.save()
        profile_status = self.is_profile_complete
        email_status = self.user.verified_account.get_verified_status()
        if not profile_status or not email_status:
            return False
        if self.referred_by !=None:
            referral,_  = ValidReferral.objects.get_or_create(by=self.referred_by, to=self)
            return True
    
class ValidReferral(models.Model):
    by=models.ForeignKey(Profile,on_delete=models.CASCADE,related_name="referred_people")
    to=models.OneToOneField(Profile,on_delete=models.CASCADE,related_name="referral")

    class Meta:
        unique_together = ('by','to')

    def __str__(self):
        return self.by+" referred "+self.to

class Team(models.Model):
    name=models.CharField(max_length=100)
    event=models.ForeignKey(Event,on_delete=models.CASCADE)
    members=models.ManyToManyField(Profile,through='Membership',related_name="team_members")
    creator=models.ForeignKey(Profile,related_name="teams_created",on_delete=models.CASCADE)
    is_active=models.BooleanField(default=False)
    access_code = models.CharField(unique=True , max_length=10 , default='uninitialized')
 
    def __str__(self):          
        return self.name + " for event " + self.event

    def total_members(self):
        return Membership.objects.filter(team=self).count()

    def join_team(self, user, acc_code):
        if acc_code == self.access_code and self.total_members() < self.event.max_members:
            if self.total_members() +1 >= self.event.min_members:
                self.is_active=True
                self.save()
            
            return Membership.objects.create(team=self,profile=user)
        
        else :
            raise(ValidationError("Maximum Size of Team reached"))

    def leave_team(self , user):
        if user == self.creator:
            self.delete()
        else:
            if self.total_members() <= self.event.min_members:
                self.is_active=False
                self.save()

            ins  = Membership.objects.get(team=self,profile=user)
            ins.delete()

class Membership(models.Model):
    team=models.ForeignKey(Team,on_delete=models.CASCADE)
    profile=models.ForeignKey(Profile,on_delete=models.CASCADE)    

    class Meta:
        unique_together = ("team","profile")


    def __str__(self):
        return self.profile+" from team "+ self.team