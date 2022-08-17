import sendgrid
import os
from sendgrid.helpers.mail import Mail, Email, To, Content

def sendgridmail(user,TEXT):   
    sg = sendgrid.SendGridAPIClient('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')
    from_email = Email("Student Setu <frompython28@gmail.com>") # Change to your verified sender
    to_email = To(user)  # Change to your recipient
    subject = "Student Setu"
    content = Content("text/plain",TEXT)
    try:
        mail = Mail(from_email, to_email, subject, content)
        # Get a JSON-ready representation of the Mail object
        mail_json = mail.get()
        # Send an HTTP POST request to /mail/send
        sg.client.mail.send.post(request_body=mail_json)
        return 1
    except Exception:
        return 0
    

