from django.shortcuts import render, redirect, reverse
from . import forms, models
from django.db.models import Sum
from django.contrib.auth.models import Group, User
from django.http import HttpResponseRedirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.conf import settings
from django.core.mail import send_mail


def home_view(request):
    if request.user.is_authenticated:
        return redirect('afterlogin')
    return render(request, 'school/index.html')


# for showing signup/login button for admin
def adminclick_view(request):
    if request.user.is_authenticated:
        return redirect('afterlogin')
    return render(request, 'school/adminclick.html')


# for showing signup/login button for teacher
def teacherclick_view(request):
    if request.user.is_authenticated:
        return redirect('afterlogin')
    return render(request, 'school/teacherclick.html')


# for showing signup/login button for student
def studentclick_view(request):
    if request.user.is_authenticated:
        return redirect('afterlogin')
    return render(request, 'school/studentclick.html')


def admin_signup_view(request):
    form = forms.AdminSigupForm()
    if request.method == 'POST':
        form = forms.AdminSigupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(user.password)
            user.save()

            my_admin_group = Group.objects.get_or_create(name='ADMIN')
            my_admin_group[0].user_set.add(user)

            return redirect('adminlogin')
    return render(request, 'school/adminsignup.html', {'form': form})


def student_signup_view(request):
    form1 = forms.StudentUserForm()
    form2 = forms.StudentExtraForm()
    mydict = {'form1': form1, 'form2': form2}
    if request.method == 'POST':
        form1 = forms.StudentUserForm(request.POST)
        form2 = forms.StudentExtraForm(request.POST)
        if form1.is_valid() and form2.is_valid():
            user = form1.save(commit=False)
            user.set_password(user.password)
            user.save()

            f2 = form2.save(commit=False)
            f2.user = user
            f2.save()

            my_student_group = Group.objects.get_or_create(name='STUDENT')
            my_student_group[0].user_set.add(user)

            return redirect('studentlogin')
        else:
            mydict = {'form1': form1, 'form2': form2}
    return render(request, 'school/studentsignup.html', context=mydict)


def teacher_signup_view(request):
    form1 = forms.TeacherUserForm()
    form2 = forms.TeacherExtraForm()
    mydict = {'form1': form1, 'form2': form2}
    if request.method == 'POST':
        form1 = forms.TeacherUserForm(request.POST)
        form2 = forms.TeacherExtraForm(request.POST)
        if form1.is_valid() and form2.is_valid():
            user = form1.save(commit=False)
            user.set_password(user.password)
            user.save()

            f2 = form2.save(commit=False)
            f2.user = user
            f2.save()

            my_teacher_group = Group.objects.get_or_create(name='TEACHER')
            my_teacher_group[0].user_set.add(user)

            return redirect('teacherlogin')
        else:
            mydict = {'form1': form1, 'form2': form2}
    return render(request, 'school/teachersignup.html', context=mydict)


# for checking user is teacher, student or admin
def is_admin(user):
    return user.groups.filter(name='ADMIN').exists()


def is_teacher(user):
    return user.groups.filter(name='TEACHER').exists()


def is_student(user):
    return user.groups.filter(name='STUDENT').exists()


def afterlogin_view(request):
    if is_admin(request.user):
        return redirect('admin-dashboard')
    elif is_teacher(request.user):
        accountapproval = models.TeacherExtra.objects.filter(user_id=request.user.id, status=True)
        if accountapproval.exists():
            return redirect('teacher-dashboard')
        else:
            return render(request, 'school/teacher_wait_for_approval.html')
    elif is_student(request.user):
        accountapproval = models.StudentExtra.objects.filter(user_id=request.user.id, status=True)
        if accountapproval.exists():
            return redirect('student-dashboard')
        else:
            return render(request, 'school/student_wait_for_approval.html')
    return redirect('/')


def logout_view(request):
    logout(request)
    return redirect('/')


# admin dashboard
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_dashboard_view(request):
    teachercount = models.TeacherExtra.objects.filter(status=True).count()
    pendingteachercount = models.TeacherExtra.objects.filter(status=False).count()

    studentcount = models.StudentExtra.objects.filter(status=True).count()
    pendingstudentcount = models.StudentExtra.objects.filter(status=False).count()

    teachersalary = models.TeacherExtra.objects.filter(status=True).aggregate(Sum('salary'))['salary__sum'] or 0
    pendingteachersalary = models.TeacherExtra.objects.filter(status=False).aggregate(Sum('salary'))['salary__sum'] or 0

    studentfee = models.StudentExtra.objects.filter(status=True).aggregate(Sum('fee'))['fee__sum'] or 0
    pendingstudentfee = models.StudentExtra.objects.filter(status=False).aggregate(Sum('fee'))['fee__sum'] or 0

    notice = models.Notice.objects.all().order_by('-date')

    mydict = {
        'teachercount': teachercount,
        'pendingteachercount': pendingteachercount,
        'studentcount': studentcount,
        'pendingstudentcount': pendingstudentcount,
        'teachersalary': teachersalary,
        'pendingteachersalary': pendingteachersalary,
        'studentfee': studentfee,
        'pendingstudentfee': pendingstudentfee,
        'notice': notice
    }
    return render(request, 'school/admin_dashboard.html', context=mydict)


# teacher section by admin
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_teacher_view(request):
    return render(request, 'school/admin_teacher.html')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_teacher_view(request):
    form1 = forms.TeacherUserForm()
    form2 = forms.TeacherExtraForm()
    mydict = {'form1': form1, 'form2': form2}
    if request.method == 'POST':
        form1 = forms.TeacherUserForm(request.POST)
        form2 = forms.TeacherExtraForm(request.POST)
        if form1.is_valid() and form2.is_valid():
            user = form1.save(commit=False)
            user.set_password(user.password)
            user.save()

            f2 = form2.save(commit=False)
            f2.user = user
            f2.status = True
            f2.save()

            my_teacher_group = Group.objects.get_or_create(name='TEACHER')
            my_teacher_group[0].user_set.add(user)

            return redirect('admin-teacher')
        else:
            mydict = {'form1': form1, 'form2': form2}
    return render(request, 'school/admin_add_teacher.html', context=mydict)


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_teacher_view(request):
    teachers = models.TeacherExtra.objects.filter(status=True)
    return render(request, 'school/admin_view_teacher.html', {'teachers': teachers})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_approve_teacher_view(request):
    teachers = models.TeacherExtra.objects.filter(status=False)
    return render(request, 'school/admin_approve_teacher.html', {'teachers': teachers})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_teacher_view(request, pk):
    teacher = models.TeacherExtra.objects.filter(id=pk).first()
    if teacher:
        teacher.status = True
        teacher.save()
    return redirect('admin-approve-teacher')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def delete_teacher_view(request, pk):
    teacher = models.TeacherExtra.objects.filter(id=pk).first()
    if teacher:
        User.objects.filter(id=teacher.user_id).delete()
    return redirect('admin-approve-teacher')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def delete_teacher_from_school_view(request, pk):
    teacher = models.TeacherExtra.objects.filter(id=pk).first()
    if teacher:
        User.objects.filter(id=teacher.user_id).delete()
    return redirect('admin-view-teacher')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def update_teacher_view(request, pk):
    teacher = models.TeacherExtra.objects.filter(id=pk).first()
    if not teacher:
        return redirect('admin-view-teacher')
    user = User.objects.filter(id=teacher.user_id).first()
    if not user:
        return redirect('admin-view-teacher')

    form1 = forms.TeacherUserUpdateForm(instance=user)
    form2 = forms.TeacherExtraForm(instance=teacher)
    mydict = {'form1': form1, 'form2': form2}

    if request.method == 'POST':
        form1 = forms.TeacherUserUpdateForm(request.POST, instance=user)
        form2 = forms.TeacherExtraForm(request.POST, instance=teacher)
        if form1.is_valid() and form2.is_valid():
            original_password = User.objects.get(id=user.id).password
            saved_user = form1.save(commit=False)
            new_password = form1.cleaned_data.get('password')
            if new_password:
                saved_user.set_password(new_password)
            else:
                saved_user.password = original_password
            saved_user.save()

            f2 = form2.save(commit=False)
            f2.status = True
            f2.save()
            return redirect('admin-view-teacher')
        else:
            mydict = {'form1': form1, 'form2': form2}
    return render(request, 'school/admin_update_teacher.html', context=mydict)


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_teacher_salary_view(request):
    teachers = models.TeacherExtra.objects.filter(status=True)
    return render(request, 'school/admin_view_teacher_salary.html', {'teachers': teachers})


# student section by admin
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_student_view(request):
    return render(request, 'school/admin_student.html')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_add_student_view(request):
    form1 = forms.StudentUserForm()
    form2 = forms.StudentExtraForm()
    mydict = {'form1': form1, 'form2': form2}
    if request.method == 'POST':
        form1 = forms.StudentUserForm(request.POST)
        form2 = forms.StudentExtraForm(request.POST)
        if form1.is_valid() and form2.is_valid():
            user = form1.save(commit=False)
            user.set_password(user.password)
            user.save()

            f2 = form2.save(commit=False)
            f2.user = user
            f2.status = True
            f2.save()

            my_student_group = Group.objects.get_or_create(name='STUDENT')
            my_student_group[0].user_set.add(user)

            return redirect('admin-student')
        else:
            mydict = {'form1': form1, 'form2': form2}
    return render(request, 'school/admin_add_student.html', context=mydict)


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_student_view(request):
    students = models.StudentExtra.objects.filter(status=True)
    return render(request, 'school/admin_view_student.html', {'students': students})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def delete_student_from_school_view(request, pk):
    student = models.StudentExtra.objects.filter(id=pk).first()
    if student:
        User.objects.filter(id=student.user_id).delete()
    return redirect('admin-view-student')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def delete_student_view(request, pk):
    student = models.StudentExtra.objects.filter(id=pk).first()
    if student:
        User.objects.filter(id=student.user_id).delete()
    return redirect('admin-approve-student')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def update_student_view(request, pk):
    student = models.StudentExtra.objects.filter(id=pk).first()
    if not student:
        return redirect('admin-view-student')
    user = User.objects.filter(id=student.user_id).first()
    if not user:
        return redirect('admin-view-student')

    form1 = forms.StudentUserUpdateForm(instance=user)
    form2 = forms.StudentExtraForm(instance=student)
    mydict = {'form1': form1, 'form2': form2}

    if request.method == 'POST':
        form1 = forms.StudentUserUpdateForm(request.POST, instance=user)
        form2 = forms.StudentExtraForm(request.POST, instance=student)
        if form1.is_valid() and form2.is_valid():
            original_password = User.objects.get(id=user.id).password
            saved_user = form1.save(commit=False)
            new_password = form1.cleaned_data.get('password')
            if new_password:
                saved_user.set_password(new_password)
            else:
                saved_user.password = original_password
            saved_user.save()

            f2 = form2.save(commit=False)
            f2.status = True
            f2.save()
            return redirect('admin-view-student')
        else:
            mydict = {'form1': form1, 'form2': form2}
    return render(request, 'school/admin_update_student.html', context=mydict)


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_approve_student_view(request):
    students = models.StudentExtra.objects.filter(status=False)
    return render(request, 'school/admin_approve_student.html', {'students': students})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def approve_student_view(request, pk):
    student = models.StudentExtra.objects.filter(id=pk).first()
    if student:
        student.status = True
        student.save()
    return redirect('admin-approve-student')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_student_fee_view(request):
    students = models.StudentExtra.objects.filter(status=True)
    return render(request, 'school/admin_view_student_fee.html', {'students': students})


# attendance related views by admin
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_attendance_view(request):
    return render(request, 'school/admin_attendance.html')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_take_attendance_view(request, cl):
    students = models.StudentExtra.objects.filter(cl=cl, status=True).order_by('roll')
    aform = forms.AttendanceForm()
    if request.method == 'POST':
        form = forms.AttendanceForm(request.POST)
        if form.is_valid():
            attendances = request.POST.getlist('present_status')
            date = form.cleaned_data['date']
            for i in range(min(len(attendances), len(students))):
                models.Attendance.objects.update_or_create(
                    date=date,
                    cl=cl,
                    roll=students[i].roll,
                    defaults={'present_status': attendances[i]}
                )
            return redirect('admin-attendance')
    return render(request, 'school/admin_take_attendance.html', {'students': students, 'aform': aform})


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_attendance_view(request, cl):
    form = forms.AskDateForm()
    if request.method == 'POST':
        form = forms.AskDateForm(request.POST)
        if form.is_valid():
            date = form.cleaned_data['date']
            attendancedata = models.Attendance.objects.filter(date=date, cl=cl)
            studentdata = models.StudentExtra.objects.filter(cl=cl, status=True).order_by('roll')
            att_dict = {a.roll: a.present_status for a in attendancedata}
            mylist = [({'present_status': att_dict.get(s.roll, 'Not Marked')}, s) for s in studentdata]
            return render(request, 'school/admin_view_attendance_page.html', {'cl': cl, 'mylist': mylist, 'date': date})
    return render(request, 'school/admin_view_attendance_ask_date.html', {'cl': cl, 'form': form})


# fee related views by admin
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_fee_view(request):
    return render(request, 'school/admin_fee.html')


@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_view_fee_view(request, cl):
    feedetails = models.StudentExtra.objects.filter(cl=cl)
    return render(request, 'school/admin_view_fee.html', {'feedetails': feedetails, 'cl': cl})


# notice related view by admin
@login_required(login_url='adminlogin')
@user_passes_test(is_admin)
def admin_notice_view(request):
    form = forms.NoticeForm()
    if request.method == 'POST':
        form = forms.NoticeForm(request.POST)
        if form.is_valid():
            notice_obj = form.save(commit=False)
            notice_obj.by = request.user.first_name or request.user.username or 'Admin'
            notice_obj.save()
            return redirect('admin-dashboard')
    return render(request, 'school/admin_notice.html', {'form': form})


# teacher section
@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_dashboard_view(request):
    teacherdata = models.TeacherExtra.objects.filter(status=True, user_id=request.user.id).first()
    if not teacherdata:
        return render(request, 'school/teacher_wait_for_approval.html')
    notice = models.Notice.objects.all().order_by('-date')
    mydict = {
        'salary': teacherdata.salary,
        'mobile': teacherdata.mobile,
        'date': teacherdata.joindate,
        'notice': notice
    }
    return render(request, 'school/teacher_dashboard.html', context=mydict)


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_attendance_view(request):
    return render(request, 'school/teacher_attendance.html')


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_take_attendance_view(request, cl):
    students = models.StudentExtra.objects.filter(cl=cl, status=True).order_by('roll')
    aform = forms.AttendanceForm()
    if request.method == 'POST':
        form = forms.AttendanceForm(request.POST)
        if form.is_valid():
            attendances = request.POST.getlist('present_status')
            date = form.cleaned_data['date']
            for i in range(min(len(attendances), len(students))):
                models.Attendance.objects.update_or_create(
                    date=date,
                    cl=cl,
                    roll=students[i].roll,
                    defaults={'present_status': attendances[i]}
                )
            return redirect('teacher-attendance')
    return render(request, 'school/teacher_take_attendance.html', {'students': students, 'aform': aform})


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_view_attendance_view(request, cl):
    form = forms.AskDateForm()
    if request.method == 'POST':
        form = forms.AskDateForm(request.POST)
        if form.is_valid():
            date = form.cleaned_data['date']
            attendancedata = models.Attendance.objects.filter(date=date, cl=cl)
            studentdata = models.StudentExtra.objects.filter(cl=cl, status=True).order_by('roll')
            att_dict = {a.roll: a.present_status for a in attendancedata}
            mylist = [({'present_status': att_dict.get(s.roll, 'Not Marked')}, s) for s in studentdata]
            return render(request, 'school/teacher_view_attendance_page.html', {'cl': cl, 'mylist': mylist, 'date': date})
    return render(request, 'school/teacher_view_attendance_ask_date.html', {'cl': cl, 'form': form})


@login_required(login_url='teacherlogin')
@user_passes_test(is_teacher)
def teacher_notice_view(request):
    form = forms.NoticeForm()
    if request.method == 'POST':
        form = forms.NoticeForm(request.POST)
        if form.is_valid():
            notice_obj = form.save(commit=False)
            notice_obj.by = request.user.first_name or request.user.username or 'Teacher'
            notice_obj.save()
            return redirect('teacher-dashboard')
    return render(request, 'school/teacher_notice.html', {'form': form})


# student section
@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_dashboard_view(request):
    studentdata = models.StudentExtra.objects.filter(status=True, user_id=request.user.id).first()
    if not studentdata:
        return render(request, 'school/student_wait_for_approval.html')
    notice = models.Notice.objects.all().order_by('-date')
    mydict = {
        'roll': studentdata.roll,
        'mobile': studentdata.mobile,
        'fee': studentdata.fee,
        'notice': notice
    }
    return render(request, 'school/student_dashboard.html', context=mydict)


@login_required(login_url='studentlogin')
@user_passes_test(is_student)
def student_attendance_view(request):
    form = forms.AskDateForm()
    if request.method == 'POST':
        form = forms.AskDateForm(request.POST)
        if form.is_valid():
            date = form.cleaned_data['date']
            studentdata = models.StudentExtra.objects.filter(user_id=request.user.id, status=True).first()
            if not studentdata:
                return render(request, 'school/student_wait_for_approval.html')
            attendancedata = models.Attendance.objects.filter(date=date, cl=studentdata.cl, roll=studentdata.roll).first()
            status = attendancedata.present_status if attendancedata else 'Not Marked'
            mylist = [({'present_status': status}, studentdata)]
            return render(request, 'school/student_view_attendance_page.html', {'mylist': mylist, 'date': date})
    return render(request, 'school/student_view_attendance_ask_date.html', {'form': form})


# about us and contact us
def aboutus_view(request):
    return render(request, 'school/aboutus.html')


def contactus_view(request):
    sub = forms.ContactusForm()
    if request.method == 'POST':
        sub = forms.ContactusForm(request.POST)
        if sub.is_valid():
            email = sub.cleaned_data['Email']
            name = sub.cleaned_data['Name']
            message = sub.cleaned_data['Message']
            try:
                send_mail(str(name) + ' || ' + str(email), message, settings.EMAIL_HOST_USER, settings.EMAIL_RECEIVING_USER, fail_silently=True)
            except Exception:
                pass
            return render(request, 'school/contactussuccess.html')
    return render(request, 'school/contactus.html', {'form': sub})

