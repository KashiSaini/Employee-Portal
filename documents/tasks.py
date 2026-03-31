import logging

from celery import shared_task
from django.contrib.auth import get_user_model

from .services import generate_salary_slip_pdf_and_email


logger = logging.getLogger(__name__)


@shared_task(ignore_result=True)
def generate_salary_slip_email_task(user_id, year, month):
    user = get_user_model().objects.get(pk=user_id)
    slip = generate_salary_slip_pdf_and_email(user=user, year=year, month=month)
    logger.info(
        "Generated salary slip %s and emailed %s for %s %s.",
        slip.pk,
        user.email,
        slip.get_month_display(),
        slip.year,
    )
    return {
        "status": "sent",
        "salary_slip_id": slip.pk,
        "user_id": user.id,
        "email": user.email,
    }
