from ..database.database import Base
from sqlalchemy import Column,Integer,BOOLEAN,String,ForeignKey,UniqueConstraint
from sqlalchemy.types import TIMESTAMP
from sqlalchemy.sql.expression import text
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)
    username = Column(String, nullable=False, unique=True, index=True)
    role = Column(String, nullable=False, server_default='Member')
    is_verified = Column(BOOLEAN, nullable=False, server_default='false')
    is_active = Column(BOOLEAN, nullable=False, server_default='true')    
    is_banned = Column(BOOLEAN, nullable=False, server_default='false')
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    applications = relationship("Application", back_populates="user")
    memberships = relationship("ProjectMember", back_populates="user")
    assigned_tasks = relationship("Task", foreign_keys="Task.assigned_to", back_populates="assignee")
    created_tasks = relationship("Task", foreign_keys="Task.created_by", back_populates="creator")
    comments = relationship("Comment", back_populates="user")
    messages = relationship("Message", back_populates="user")


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer,primary_key=True,nullable=False)
    title = Column(String,nullable=False)
    description = Column(String,nullable=False)
    tech_stack = Column(String,nullable=False)
    required_roles = Column(String,nullable=False)
    max_members = Column(Integer,server_default=text('5'))
    status = Column(String,nullable=False,server_default="open")
    owner_id = Column(Integer,ForeignKey("users.id",ondelete="Cascade"),nullable = False)
    created_at = Column(TIMESTAMP(timezone=True),nullable=False,server_default=text('now()'))
    applications = relationship("Application",back_populates="project")
    members = relationship("ProjectMember",back_populates="project")
    tasks = relationship("Task", back_populates="project")
    messages = relationship("Message", back_populates="project")


class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer,primary_key=True,nullable=False)
    project_id = Column(Integer,ForeignKey("projects.id",ondelete="Cascade"),nullable = False)
    user_id = Column(Integer,ForeignKey("users.id",ondelete="Cascade"),nullable = False)
    message = Column(String,nullable = False)
    status = Column(String , nullable = False,server_default="pending")
    created_at = Column(TIMESTAMP(timezone=True),nullable =False,server_default=text('now()'))
    project = relationship("Project", back_populates="applications")
    user = relationship("User", back_populates="applications")



class ProjectMember(Base):
    __tablename__ = "projectmembers"

    __table_args__ = ( UniqueConstraint("project_id","user_id"),)



    id = Column(Integer,primary_key=True,nullable=False)
    project_id = Column(Integer,ForeignKey("projects.id",ondelete="Cascade"),nullable = False)
    user_id = Column(Integer,ForeignKey("users.id",ondelete="Cascade"),nullable = False)
    role = Column(String,nullable = False,server_default="member")
    joined_at = Column(TIMESTAMP(timezone=True),nullable = False,server_default=text('now()'))
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="memberships")


class Task(Base):
    __tablename__ =  "tasks"

    id=Column(Integer,primary_key=True,nullable = False)
    project_id = Column(Integer,ForeignKey("projects.id",ondelete="Cascade"),nullable = False)
    title = Column(String,nullable=False)
    description = Column(String,nullable=True)
    status = Column(String , nullable = False,server_default="todo")
    assigned_to = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_by  = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at  = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('now()'))

    project  = relationship("Project", back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_tasks")
    creator  = relationship("User", foreign_keys=[created_by],  back_populates="created_tasks")
    comments = relationship("Comment",back_populates="task")

class Comment(Base):
    __tablename__ = "comments"

    id=Column(Integer,primary_key=True,nullable = False)
    task_id = Column(Integer,ForeignKey("tasks.id",ondelete = "Cascade"),nullable = False)
    user_id = Column(Integer,ForeignKey("users.id",ondelete = "Cascade"),nullable = False)
    content = Column(String,nullable=False)
    created_at = Column(TIMESTAMP(timezone=True),nullable =False,server_default= text("now()"))

    user = relationship("User",back_populates="comments")
    task = relationship("Task",back_populates="comments")





class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    project = relationship("Project", back_populates="messages")
    user = relationship("User", back_populates="messages")




class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, nullable=False)
    token = Column(String, nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))

    user = relationship("User")