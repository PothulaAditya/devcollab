from fastapi import FastAPI
from .routers import auth, user, project, application, projectmember, task, comment, chat, admin


app = FastAPI()
 

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(project.router)
app.include_router(application.router)
app.include_router(projectmember.router)
app.include_router(task.router)
app.include_router(comment.router)
app.include_router(chat.router)
app.include_router(admin.router)











