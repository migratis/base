from django.http import JsonResponse, FileResponse
from django.core.exceptions import ValidationError
from typing import List
from ninja import Form, File, Router
from ninja.files import UploadedFile
from migratis.api.functions import formatErrors
from . import models, schemas
from migratis.user.models import User
from pprint import pprint

router = Router()

@router.get('/topics', auth=None, response=List[schemas.TopicSchema])
def getTopicList(request):
    try:
        topics = models.Topic.objects.all()
    except(TypeError, ValueError, OverflowError, models.Topic.DoesNotExist):
        topics = None
    if topics is not None:
        return topics
    return JsonResponse({"detail": formatErrors({"topic": ["topic-not-exists"]})}, status=422)

@router.post('/offline', auth=None)
def offlineSupport(request, support: Form[schemas.TicketSchemaIn]):
    try:
        try:
            support.user = User.objects.get(email=support.contact)
        except models.Topic.DoesNotExist:
            support.user = None
        if support.topic == 0:
            if support.object == None:
                return JsonResponse({"detail": formatErrors({"object": ["empty-field"]})}, status=422)
            support.topic = None
        else:
            support.topic = models.Topic.objects.get(pk=support.topic)
        ticket = models.Ticket(**support.dict())         
        ticket.save()
        return JsonResponse({"detail": [{"success": ["ticket-successfully-send"]}]})
    except ValidationError as e:
        if (ticket.id is not None): ticket.delete()
        return JsonResponse({"detail": formatErrors(e.message_dict)}, status=422)
    
@router.post('/ticket/create')
def createTicket(request, ticket: Form[schemas.TicketSchemaIn]):
    try:
        userId = request.user.id
        user = models.User.objects.get(pk=userId)
        ticket.user = user
        if ticket.topic == 0:
            if ticket.object == None:
                return JsonResponse({"detail": formatErrors({"object": ["empty-field"]})}, status=422)
            ticket.topic = None
        else:
            try:
                ticket.topic = models.Topic.objects.get(pk=ticket.topic)     
            except models.Topic.DoesNotExist:
                return JsonResponse({"detail": formatErrors({"topic": ["empty-field"]})}, status=422)       
        new_ticket = models.Ticket(**ticket.dict())         
        new_ticket.save()
        return JsonResponse({"detail": [{"success": ["ticket-successfully-saved"]}]})
    except ValidationError as e:
        if (new_ticket.id is not None): new_ticket.delete()
        return JsonResponse({"detail": formatErrors(e.message_dict)}, status=422)
        
@router.post('/ticket/update/{id}')  
def updateTicket(request, id: int, ticket: Form[schemas.TicketSchemaIn]):        
    try:
        userId = request.user.id
        existing_ticket = models.Ticket.objects.get(user=userId, pk=id)
        if ticket.status == 'c':
            return JsonResponse({"detail": [{"error": ["ticket-already-closed"]}]})                
        if ticket.topic == 0:
            if ticket.object == None:
                return JsonResponse({"detail": formatErrors({"object": ["empty-field"]})}, status=422)
            ticket.topic = None
        else:
            ticket.topic = models.Topic.objects.get(pk=ticket.topic)
        existing_ticket.topic = ticket.topic
        existing_ticket.object = ticket.object
        existing_ticket.content = ticket.content
        existing_ticket.save()
        return JsonResponse({"detail": [{"success": ["ticket-successfully-updated"]}]})
    except ValidationError as e:
        return JsonResponse({"detail": formatErrors(e.message_dict)}, status=422)
    
@router.get('/ticket/close/{id}')    
def closeTicket(request, id: int):        
    try:
        userId = request.user.id
        existing_ticket = models.Ticket.objects.get(user=userId, pk=id)
        existing_ticket.status = 'c'
        existing_ticket.save()
        return JsonResponse({"detail": [{"success": ["ticket-successfully-closed"]}]})
    except (ValidationError, models.Ticket.DoesNotExist) as e:
        return JsonResponse({"detail": formatErrors(e.message_dict)}, status=422)
    
@router.post('/{ticket_id}/thread/create')
def createThread(request, ticket_id: int, thread : Form[schemas.ThreadSchemaCreate]):
    try:
        userId = request.user.id
        user = models.User.objects.get(pk=userId)
        ticket = models.Ticket.objects.get(pk=ticket_id)
        if ticket.status == 'c':
            return JsonResponse({"detail": [{"error": ["ticket-already-closed"]}]}) 
        thread.user = user
        thread.replier = user
        thread.ticket = ticket
        new_thread = models.Thread(**thread.dict())         
        new_thread.save()
        return JsonResponse({"detail": [{"success": ["thread-successfully-saved"]}]})
    except ValidationError as e:
        if (new_thread.id is not None): new_thread.delete()
        return JsonResponse({"detail": formatErrors(e.message_dict)}, status=422)
        
@router.post('/thread/update/{id}')
def updateThread(request, id: int, thread: Form[schemas.ThreadSchemaUpdate]):
    try:
        userId = request.user.id
        existing_thread = models.Thread.objects.get(user=userId, pk=id)
        if existing_thread.replied:
            return JsonResponse({"detail": [{"error": ["thread-not-updated"]}]})
        if existing_thread.ticket.status == 'c':
            return JsonResponse({"detail": [{"error": ["ticket-already-closed"]}]})
        for attr, value in thread.dict().items():
            if attr != 'user' and attr != 'replier':
                setattr(existing_thread, attr, value)
        existing_thread.save()
        return JsonResponse({"detail": [{"success": ["thread-successfully-updated"]}]})
    except ValidationError as e:
        return JsonResponse({"detail": formatErrors(e.message_dict)}, status=422)
    
@router.get('/ticket/list', response=List[schemas.TicketSchemaOut])
def getTickets(request):
    try:
        userId = request.user.id
        tickets = models.Ticket.objects.filter(user=userId).select_related('user', 'topic')
    except(TypeError, ValueError, OverflowError, models.Ticket.DoesNotExist):
        tickets = None
    if tickets is not None:
        return tickets            
    return JsonResponse({}) 

@router.get('/tickets', response=List[schemas.TicketSchemaOut])
def getFullTickets(request):
    try:
        userId = request.user.id
        tickets = models.Ticket.objects.filter(user=userId).select_related('user', 'topic').order_by('-cdate')
        for ticket in tickets:
            ticket.threads = models.Thread.objects.filter(user=userId, ticket=ticket.id).select_related('user', 'replier', 'ticket').order_by('cdate')
            ticket.files = models.File.objects.filter(user=userId, ticket=ticket.id).select_related('user', 'uploader', 'ticket').order_by('cdate')
    except(TypeError, ValueError, OverflowError, models.Ticket.DoesNotExist):
        tickets = None
    if tickets is not None:
        return tickets            
    return JsonResponse({})

@router.get('/ticket/{id}', response=schemas.TicketSchemaOut) 
def getTicket(request, id: int):
    userId = request.user.id
    try:
        ticket = models.Ticket.objects.filter(user=userId).get(pk=id)
    except(TypeError, ValueError, OverflowError, models.Ticket.DoesNotExist):
        ticket = None              
    
    return ticket
        
@router.get('/{ticket_id}/threads', response=schemas.TicketSchemaOut)   
def getTicketThreads(request, ticket_id: int):
    userId = request.user.id  
    try:
        ticket = models.Ticket.objects.get(user=userId, pk=ticket_id)
        ticket.threads = models.Thread.objects.filter(user=userId, ticket=ticket.id).select_related('user', 'ticket')
        ticket.files = models.File.objects.filter(user=userId, ticket=ticket.id).select_related('user', 'uploader', 'ticket').order_by('cdate')
    except models.Ticket.DoesNotExist:
        return 204, None   
    threads = models.Thread.objects.filter(user=userId, ticket=ticket_id)
    class result: pass
    result.ticket = ticket
    result.threads = threads
    return result
    
@router.get('/thread/{id}', response=schemas.ThreadSchemaOut)  
def getThread(request, id: int):
    try:
        userId = request.user.id
        thread = models.Thread.objects.get(user=userId, pk=id)
        thread.files = models.File.objects.filter(user=userId, thread=thread.id).select_related('user', 'uploader', 'thread').order_by('cdate')
    except(TypeError, ValueError, OverflowError, models.Thread.DoesNotExist):
        thread = None
    if thread is not None:
        return thread            
    return JsonResponse({})

@router.post('/{ticket_id}/upload')
def uploadFile(request, ticket_id: int, file: File[UploadedFile]):
    userId = request.user.id
    user = models.User.objects.get(pk=userId)
    ticket = models.Ticket.objects.get(user=user, pk=ticket_id)
    if ticket.status == 'c':
        return JsonResponse({"detail": [{"error": ["ticket-already-closed"]}]})
    if file.content_type in [
        'text/csv', 
        'text/plain', 
        'application/vnd.oasis.opendocument.spreadsheet', 
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/xml',
        'text/xml',
        'image/jpeg',
        'image/png',
        'application/pdf',
        'application/vnd.ms-powerpoint',
        'application/vnd.openxmlformats',
        'officedocument.presentationml.presentation',
        'application/zip',
        'application/msword',
        'application/vnd.openxmlformats',
        'officedocument.wordprocessingml.document',
    ]: 
        try:
            new_file = models.File()
            new_file.user = user
            new_file.uploader = user
            new_file.ticket = ticket
            new_file.file.save(file.name, file)
            new_file.mime = file.content_type
            new_file.save()
            
            return JsonResponse({"detail": [{"success": ["file-successfully-uploaded"]}]})                
        except ValidationError as e:
            return JsonResponse({"detail": formatErrors(e.message_dict)}, status=423)                          
    else:
        return JsonResponse({"detail": formatErrors({"file": ["wrong-mimetype"]})}, status=422)
                                                  
@router.get('/download/{id}', response=schemas.FileSchemaOut)
def download(request, id: int):
    userId = request.user.id
    try:
        file = models.File.objects.get(pk=id, user=userId)
    except models.File.DoesNotExist:
        return JsonResponse({"detail": formatErrors({"file": ["file-not-exists"]})}, status=422)
    
    response =  FileResponse(file.file.open('rb'))
    response['Content-Type'] = file.mime
    response['Content-Disposition'] = 'attachment;'
    return response