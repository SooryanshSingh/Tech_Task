# TestPro – AI-Assisted Online Examination & Remote Proctoring System

TestPro is a production-grade online examination and AI-assisted remote proctoring platform built with Django, Django Channels, WebSockets, and Agora RTC.

The platform enables secure remote examinations with real-time communication between students and proctors while leveraging computer vision for automated proctoring. It combines backend-controlled exam workflows, live monitoring, audit logging, and AI-assisted violation detection in a scalable architecture.

---

# Features

## Online Examination

- Role-based authentication (Student, Test Maker, Proctor)
- Email verification for student registration
- MCQ-based examinations
- Server-controlled exam timer
- Automatic submission on timeout
- Secure result generation and storage
- Candidate assignment through invitation workflow

---

## Test Maker

- Create, edit, and delete exams
- Manage question bank
- Schedule exams
- Assign students and proctors
- View exam results and marks

---

## Student Portal

- Interactive examination dashboard
- Backend-synchronized countdown timer
- Question navigation
- Live camera streaming during examinations
- Real-time warning notifications
- Automatic exam submission
- Forced exam termination handling
- Tab-switch monitoring

---

## Real-Time Proctor Dashboard

- 1:N proctor-to-student monitoring
- Live student video feeds
- Real-time violation dashboard
- Student warning system
- Remote exam termination
- Evidence viewing
- Live audit updates

---

## AI-Assisted Proctoring

- Face verification before examination
- No-face detection
- Multiple-face detection
- Mobile phone detection using YOLOv8
- BlazeFace-based face detection
- Tab-switch detection
- Violation scoring
- Evidence capture and logging

---

## Security & Audit

- Django Groups based RBAC
- Secure WebSocket authentication
- Exam audit logs
- Environment-based configuration
- Evidence storage for violations

---

# Tech Stack

## Backend

- Django
- Django Channels
- Daphne
- PostgreSQL
- Agora RTC SDK
- WebSockets

## AI & Computer Vision

- YOLOv8
- BlazeFace (MediaPipe)
- OpenCV

## Frontend

- HTML
- CSS
- JavaScript
- Fetch API
- WebSocket API

---

# Architecture Highlights

- ASGI-based real-time backend using Django Channels
- Backend-controlled examination lifecycle
- Event-driven proctor dashboard
- Real-time bidirectional communication
- AI-assisted violation detection pipeline

---

# Environment Variables

```env
DJANGO_SECRET_KEY=
DEBUG=False
ALLOWED_HOSTS=exam.example.com

DATABASE_URL=
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1

AGORA_APP_ID=
AGORA_APP_CERTIFICATE=

EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
```

Run the web application and asynchronous report worker as separate processes:

```bash
python manage.py migrate
daphne exam.asgi:application
celery -A exam worker --loglevel=INFO
```

`requirements.in` lists direct dependencies, while `requirements.txt` is the
Python 3.12 lock file used for reproducible deployments. Regenerate the lock
after intentionally changing a direct dependency and run the Django test suite
before deployment.

Browser-side MediaPipe imports are pinned to an exact version. The application
also sends a Content Security Policy header that limits scripts and connections
to the application, Agora, and jsDelivr. Inline scripts remain temporarily
allowed for the existing templates and should be moved to static files before
removing `'unsafe-inline'` from the policy.

---

# What This Project Demonstrates

- Full-stack web development
- Real-time distributed systems
- WebSocket communication
- AI-assisted computer vision integration
- Secure authentication and authorization
- Production-ready backend architecture
- Cloud deployment readiness
- Scalable online examination workflows

---

# Design Decisions

### Why Agora instead of raw WebRTC?

Agora simplifies large-scale real-time communication by providing reliable signaling, reconnection handling, and media transport, allowing the application to focus on examination logic instead of low-level networking.

---

### Why Django Channels?

Django Channels enables HTTP requests and persistent WebSocket connections within the same framework, simplifying permission management and real-time communication.

---



### Why Backend-Controlled Timers?

Exam timing is enforced on the server to prevent client-side tampering and ensure fairness across all participants.

---

### Why Audit Logs?

Every important examination event is recorded to provide traceability, transparency, and post-exam review capability.

---

### Why AI-Assisted Proctoring?

Computer vision automatically detects suspicious behavior such as mobile phone usage, missing faces, and multiple faces, reducing manual monitoring effort while assisting human proctors.

---

# Future Improvements

- Eye-gaze estimation
- Head pose estimation
- Browser lockdown support
- Automatic reconnection after network failures
- Exam analytics dashboard
- Distributed deployment using Docker and Kubernetes
