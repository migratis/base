from django.db.models.signals import post_save
from . import models
from django.dispatch import receiver

@receiver(post_save, sender=models.Thread)
def updateThread(sender, instance, **kwargs):
    threads = models.Thread.objects.filter(
        user=instance.user.id,
        ticket=instance.ticket.id, 
        replied=False,
        cdate__lt=instance.cdate
    )
    for thread in threads:
        thread.replied = True
        thread.save()

@receiver(post_save, sender=models.Thread)
@receiver(post_save, sender=models.File)
def updateTicketMdate(sender, instance, **kwargs):
    instance.ticket.save()
                         
      