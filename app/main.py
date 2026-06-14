from fastapi import FastAPI
from .routers import auth, user, project, application, projectmember, task, comment, chat
from .celery_worker import send_email
app = FastAPI()

@app.get("/")
def route():
    return {"message": "hello world"}

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(project.router)
app.include_router(application.router)
app.include_router(projectmember.router)
app.include_router(task.router)
app.include_router(comment.router)
app.include_router(chat.router)


@app.get('/test-celery')
def test_mail():
    send_email.delay("23eg107f22@anurag.edu.in","hi raaa","hjdgqlejhvcqljehcb;qkhevcl")
    
    return {"msg":"task completes successfully"}









