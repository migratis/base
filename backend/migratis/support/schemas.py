from ninja import ModelSchema, Schema
from . import models
from migratis.user.schemas import UserSchemaOut
from migratis.i18n.schemas import TranslationKeySchema
from typing import List

class TopicSchema(ModelSchema):
    label: TranslationKeySchema

    class Meta:
        model = models.Topic
        fields = ['id', 'label']

class FileSchemaOut(ModelSchema):
    filename: str = None

    class Meta:
        model = models.File
        fields = ['id', 'user', 'uploader', 'ticket', 'file', 'mime', 'cdate']

class FileSchemaIn(ModelSchema):
    user: int = None
    ticket: int = None

    class Meta:
        model = models.File
        fields = ['user', 'uploader', 'ticket', 'file', 'cdate']

class ThreadSchemaCreate(ModelSchema):
    user: int = None
    ticket: int = None
    replier: int = None
    class Meta:
        model = models.Thread
        fields = ['user', 'ticket', 'content', 'replier']

class ThreadSchemaUpdate(ModelSchema):
    user: int = None

    class Meta:
        model = models.Thread
        fields = ['user', 'content']

class ThreadSchemaOut(ModelSchema):

    class Meta:
        model = models.Thread
        fields = ['id', 'user', 'replier', 'content', 'cdate', 'mdate', 'replied']            

class TicketSchemaIn(ModelSchema):

    class Meta:
        model = models.Ticket
        fields = ['user', 'topic', 'status', 'content', 'contact', 'object', 'language']

class TicketSchemaOut(ModelSchema):
    user: UserSchemaOut | None = None
    topic: TopicSchema | None = None
    threads: List[ThreadSchemaOut] | None = None
    files: List[FileSchemaOut] | None = None

    class Meta:
        model = models.Ticket
        fields = ['id', 'user', 'contact', 'assignee', 'topic', 'object', 'content', 'status', 'cdate', 'mdate']


