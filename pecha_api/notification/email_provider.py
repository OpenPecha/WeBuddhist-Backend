import logging
from ..config import get
from fastapi import HTTPException
from starlette import status


def send_email(to_email: str, subject: str, message: str):
    import mailtrap as mt

    mail = mt.Mail(
        sender=mt.Address(email=get('SENDER_EMAIL'), name=get('SENDER_NAME')),
        to=[mt.Address(email=to_email)],
        subject=subject,
        text=subject,
        html=message
    )
    try:
        client = mt.MailtrapClient(token=get('MAILTRAP_API_KEY'))
        response = client.send(mail)
        print(response)
    except Exception as e:
        logging.error(e)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email send failed.")
