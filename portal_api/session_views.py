from django.contrib.auth import authenticate, login, logout, get_user_model
from django.utils import timezone
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from attendance.models import DailyWorkLog

User = get_user_model()


class SessionLoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        employee_id = request.data.get("employee_id")
        password = request.data.get("password")
        work_mode = request.data.get("work_mode", "")

        if not employee_id or not password:
            return Response(
                {"detail": "Employee ID and password are required."},
                status=400
            )

        try:
            user_obj = User.objects.get(employee_id=employee_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "Invalid employee ID or password."},
                status=400
            )

        user = authenticate(request, username=user_obj.username, password=password)

        if user is None:
            return Response(
                {"detail": "Invalid employee ID or password."},
                status=400
            )

        login(request, user)
        request.session["work_mode"] = work_mode

        today = timezone.localdate()
        now = timezone.now()

        work_log, created = DailyWorkLog.objects.get_or_create(
            user=user,
            work_date=today,
            defaults={
                "first_login": now,
                "work_mode": work_mode,
            }
        )

        if not work_log.work_mode:
            work_log.work_mode = work_mode
            work_log.save(update_fields=["work_mode"])

        return Response({
            "message": "Login successful.",
            "redirect_url": "/dashboard/",
            "employee_id": user.employee_id,
            "username": user.username,
        })


class SessionLogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({
            "message": "Logged out successfully.",
            "redirect_url": "/"
        })


class SignOffAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        today = timezone.localdate()
        now = timezone.now()

        work_log, created = DailyWorkLog.objects.get_or_create(
            user=request.user,
            work_date=today,
            defaults={
                "first_login": now,
                "work_mode": request.session.get("work_mode", ""),
            }
        )

        if not work_log.is_signed_off:
            work_log.sign_off_time = now
            total_seconds = int((work_log.sign_off_time - work_log.first_login).total_seconds())
            if total_seconds < 0:
                total_seconds = 0

            work_log.total_work_seconds = total_seconds
            work_log.is_signed_off = True

            if not work_log.work_mode:
                work_log.work_mode = request.session.get("work_mode", "")

            work_log.save()

        return Response({
            "message": "Signed off successfully.",
            "work_date": str(work_log.work_date),
            "first_login": work_log.first_login.strftime("%d %b %Y %H:%M"),
            "sign_off_time": work_log.sign_off_time.strftime("%d %b %Y %H:%M") if work_log.sign_off_time else "",
            "total_work_hours": work_log.total_work_hours_display,
            "work_mode": work_log.get_work_mode_display(),
            "is_signed_off": work_log.is_signed_off,
        })