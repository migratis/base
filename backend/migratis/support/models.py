from django.contrib import admin
from django.db import models
from migratis.user.models import User, LANGUAGES
from migratis.i18n.models import TranslationKey
from django.utils.html import format_html
import os

STATUSES = [
    ("o", "open"), 
    ("p", "pending"), 
    ("c", "closed")
]

class Topic(models.Model):
    label = models.ForeignKey(TranslationKey, on_delete=models.PROTECT)

    class Meta:
        verbose_name_plural = "Topics"

    def __str__(self):
        return self.label.key

class Ticket(models.Model):
    content = models.TextField(max_length=5000, null=False)
    topic = models.ForeignKey(Topic, on_delete=models.DO_NOTHING, unique=False, null=True, blank=True)
    object = models.CharField(max_length=255, null=True, blank=True)
    contact = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, unique=False, null=True)
    cdate = models.DateTimeField(auto_now_add=True)
    mdate = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=1, choices=STATUSES, default='o')
    assignee = models.ForeignKey(User, related_name="ticket_assignees", on_delete=models.DO_NOTHING, unique=False, null=True, blank=True)
    language = models.CharField(max_length=2, choices=LANGUAGES, null=False, blank=True)

    @admin.display
    def colored_status(self):
        return format_html(
            '<span style="color: {};">{}</span>',
            "green" if self.status == 'o' else "red" if self.status =='p' else "grey",
            dict(STATUSES)[self.status]
        )
    
    @admin.display
    def topic_object(self):
        return self.topic.label.key if self.topic else self.object
        
    class Meta:
        verbose_name_plural = "Tickets"

    def __str__(self):
        return self.user.email + " " + self.content[0:20] + "... " + str(self.cdate) + " " + str(self.mdate)

class Thread(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, unique=False, null=True)
    replier = models.ForeignKey(User, related_name="thread_repliers", on_delete=models.DO_NOTHING, unique=False, null=True)    
    content = models.TextField(max_length=5000, null=False)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, unique=False,)
    cdate = models.DateTimeField(auto_now_add=True)
    mdate = models.DateTimeField(auto_now=True)
    replied = models.BooleanField(default=False)

    @admin.display
    def short_content(self):
        return self.content[0:20] + "..."

    class Meta:
        verbose_name_plural = "Threads"

    def __str__(self):
        return self.replier.email if self.replier is not None else self.user.email + " " + self.content[0:20] + "... " + str(self.cdate) + " " + str(self.mdate)
    
    def save(self,*args,**kwargs):
        if self.user is None:
            self.user = self.ticket.user
        super(Thread,self).save(*args,**kwargs)


def get_upload_path(instance, filename):
    return os.path.join(
    "migratis/support/files/user_%d" % instance.user.id, filename)

class File(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, unique=False, null=True) 
    user = models.ForeignKey(User, on_delete=models.CASCADE, unique=False, null=True)
    uploader = models.ForeignKey(User, related_name="file_uploaders", on_delete=models.DO_NOTHING, unique=False,)
    cdate = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to=get_upload_path, blank=True, null=True)
    mime = models.CharField(max_length=255)
    
    def filename(self):
        return os.path.basename(self.file.name)
    class Meta:
        verbose_name_plural = "Files"

    def __str__(self):
        return self.user.email + " " + self.uploader.email + " " + str(self.cdate)
    
    def save(self,*args,**kwargs):
        if self.user is None :
            self.user = self.ticket.user
        super(File,self).save(*args,**kwargs)