import datetime

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy import Index, Column, Boolean, Integer, Unicode, Binary, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker, relationship, backref


Base = declarative_base()

class SpookMixin(object):

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True)
    created_at = Column(Unicode, default=datetime.datetime.now, index=True)


class Experience(SpookMixin, Base):
    project = Column(Unicode, index=True)
    message = Column(Unicode, index=True)
    screenshot = Column(Unicode, index=True)
    user_initiated = Column(Boolean, index=True)
    ignored = Column(Boolean, index=True)
    after_break = Column(Boolean, index=True)

    def __init__(self, project, message, screenshot, user_initiated = True, ignored = False, after_break = False):
        self.project = project
        self.message = message
        self.screenshot = screenshot
        self.user_initiated = user_initiated
        self.ignored = ignored
        self.after_break = after_break

    def __repr__(self):
        return "<Experience message: '%s'>" % self.message


class Debrief(SpookMixin, Base):
    experience_id = Column(Integer, ForeignKey('experience.id'), nullable=False, index=True)
    experience = relationship("Experience", backref=backref('debrief'))

    doing_report = Column(Unicode, index=True)
    audio_file = Column(Unicode, index=True)
    memory_id = Column(Integer, index=True)
    # memory_strength = Column(Unicode, index=True)

    def __init__(self, experience_id, doing_report, audio_file, memory_id):
        self.experience_id = experience_id
        self.doing_report = doing_report
        self.audio_file = audio_file
        self.memory_id = memory_id
        # self.memory_strength = memory_strength

    def __repr__(self):
        return "<Participant was: '%s'>" % self.doing_report



class Cue(SpookMixin, Base):

    # experience_id = Column(Integer, ForeignKey('experience.id'), nullable=False, index=True)
    # experience = relationship("Experience", backref=backref('cue'))
    # debrief_id = Column(Integer, ForeignKey('debrief.id'), nullable=False, index=True)
    # debrief = relationship("Debrief", backref=backref('cue'))


    cue_size = Column(Integer)
    cue_extent = Column(Unicode)
    cue_type = Column(Unicode)
    animation_span = Column(Integer)
    animation_adjacency = Column(Unicode)
    animation_type = Column(Unicode)
    animation_speed = Column(Integer)

    audio = Column(Unicode)

    def __init__(self, cue_size, cue_extent, cue_type, animation_span, animation_adjacency, animation_type, animation_speed, audio):
        self.cue_size = cue_size
        self.cue_extent = cue_extent
        self.cue_type = cue_type
        self.animation_span = animation_span
        self.animation_adjacency = animation_adjacency
        self.animation_type = animation_type
        self.animation_speed = animation_speed
        self.audio = audio

    def __repr__(self):
        return "<Cue(size='%s', extent='%s')>" % (self.cue_size, self.cue_extent)
