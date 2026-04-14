from django.contrib import admin
from django.forms.models import BaseInlineFormSet
from . import models
from django.core.mail import EmailMessage
from django.conf import settings
from smtplib import SMTPRecipientsRefused
from django.template.loader import render_to_string
from migratis.i18n.views import t
from pprint import pprint


@admin.register(models.Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("label",)
    search_fields = ('label',)

class FileFormset(BaseInlineFormSet):
    def save_new(self, form, commit=True):
        obj = super(FileFormset, self).save_new(form, commit=False)
        obj.uploader = self.request.user
        for file in self.request._files:
            mime = self.request._files[file].content_type
            obj.mime = mime
        if commit:
            obj.save()
        return obj

class FileInline(admin.TabularInline):
    model = models.File
    fields = ( "user", "ticket", "file",)
    readonly_fields = ( "user", "ticket", ) 
    extra = 1
    formset = FileFormset

    def get_formset(self, request, obj=None, **kwargs):
        formset = super(FileInline, self).get_formset(request, obj, **kwargs)
        formset.request = request
        return formset

class ThreadFormset(BaseInlineFormSet):
    def save_new(self, form, commit=True):
        obj = super(ThreadFormset, self).save_new(form, commit=False)
        obj.replier = self.request.user
        obj.user = obj.ticket.user
        if obj.replier.id != obj.user.id:
            try:
                if obj.user:
                    email = obj.user.email
                    language = obj.user.language
                else:
                    email = obj.ticket.contact
                    language = obj.ticket.language
                if obj.ticket.topic:
                    subject = t(obj.ticket.topic.label.key, language, 'support')
                else:
                    subject = obj.ticket.object

                mail_subject = '[' + settings.SITE_NAME + '] Re: ' + subject
                message = render_to_string(language + '.reply_email.html', {
                    'support': obj,
                    'url': settings.FRONTEND_URL,
                    'app': settings.SITE_NAME,
                })
                email = EmailMessage(
                    mail_subject,
                    message,
                    from_email=settings.EMAIL_SENDER,
                    to=[email]
                )
                email.send()
            except SMTPRecipientsRefused as e:
                pass
        if commit:
            obj.save()
        return obj

class ThreadInline(admin.TabularInline):
    model = models.Thread
    fields = ( "user", "replier", "replied", "content",)
    readonly_fields = ("user", "replier", "replied",) 
    extra = 1
    formset = ThreadFormset

    def get_formset(self, request, obj=None, **kwargs):
        formset = super(ThreadInline, self).get_formset(request, obj, **kwargs)
        formset.request = request
        return formset
    
@admin.register(models.Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("mdate", "user", "assignee", "topic_object", "colored_status",)
    search_fields = ('id', 'user__email', 'assignee__email', 'content', 'topic__label', 'cdate', 'mdate',)
    list_filter = (
        'status', 
        ('assignee', admin.RelatedOnlyFieldListFilter), 
        ('topic', admin.RelatedOnlyFieldListFilter)
    )
    inlines = [
        ThreadInline,
        FileInline
    ]

    def save_model(self, request, obj, form, change):
        if not obj.assignee:
            obj.assignee = request.user
        elif obj.status != 'c' and obj.assignee != request.user and obj.assignee.is_staff and "assignee" not in form.changed_data:
            try:
                mail_subject = '[' + settings.SITE_NAME + '] ' + \
                    t('ticket-assignment', obj.assignee.language, 'support')
                message = render_to_string(obj.assignee.language + '.assignment_email.html', {
                    'ticket': obj.id,
                    'url': settings.BACKEND_URL,
                    'app': settings.SITE_NAME,
                    'user': obj.assignee,
                })
                email = EmailMessage(
                    mail_subject,
                    message,
                    from_email=settings.EMAIL_SENDER,
                    to=[obj.assignee.email]
                )
                email.send()
            except SMTPRecipientsRefused as e:
                pass
        if obj.status != 'c':
            obj.status = 'p'
        obj.save()


