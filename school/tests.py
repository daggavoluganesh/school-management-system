from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from school import models


class SchoolManagementSystemTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_group = Group.objects.create(name='ADMIN')
        self.teacher_group = Group.objects.create(name='TEACHER')
        self.student_group = Group.objects.create(name='STUDENT')

    def test_public_pages(self):
        pages = ['/', '/adminclick', '/teacherclick', '/studentclick', '/aboutus', '/contactus',
                 '/adminlogin', '/teacherlogin', '/studentlogin']
        for page in pages:
            response = self.client.get(page)
            self.assertEqual(response.status_code, 200, f"Page {page} failed with {response.status_code}")

    def test_contactus_post(self):
        response = self.client.post('/contactus', {
            'Name': 'John Tester',
            'Email': 'john@example.com',
            'Message': 'Testing contact us form'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Your message sent successfully')

    def test_admin_signup_and_dashboard(self):
        response = self.client.post('/adminsignup', {
            'first_name': 'Super',
            'last_name': 'Admin',
            'username': 'adminuser',
            'password': 'AdminPassword123!'
        })
        self.assertRedirects(response, '/adminlogin')

        login_resp = self.client.post('/adminlogin', {
            'username': 'adminuser',
            'password': 'AdminPassword123!'
        }, follow=True)
        self.assertEqual(login_resp.status_code, 200)

        dash_resp = self.client.get('/admin-dashboard')
        self.assertEqual(dash_resp.status_code, 200)
        self.assertContains(dash_resp, 'Total Teacher')

    def test_teacher_workflow_and_updates(self):
        # 1. Teacher applies
        resp = self.client.post('/teachersignup', {
            'first_name': 'Jane',
            'last_name': 'Teacher',
            'username': 'janeteacher',
            'password': 'TeacherPass123!',
            'mobile': '9876543210',
            'salary': 35000
        })
        self.assertRedirects(resp, '/teacherlogin')

        # 2. Login before approval -> wait page
        login_resp = self.client.post('/teacherlogin', {
            'username': 'janeteacher',
            'password': 'TeacherPass123!'
        }, follow=True)
        self.assertEqual(login_resp.status_code, 200)
        self.assertContains(login_resp, 'Your Account is not approved till now')

        # 3. Admin approves teacher
        admin_user = User.objects.create_user('admin2', 'a@a.com', 'pass')
        self.admin_group.user_set.add(admin_user)
        admin_client = Client()
        admin_client.force_login(admin_user)

        teacher_extra = models.TeacherExtra.objects.get(user__username='janeteacher')
        self.assertFalse(teacher_extra.status)

        approve_resp = admin_client.get(f'/approve-teacher/{teacher_extra.id}')
        self.assertRedirects(approve_resp, '/admin-approve-teacher')

        teacher_extra.refresh_from_db()
        self.assertTrue(teacher_extra.status)

        # 4. Teacher accesses dashboard after approval
        teacher_client = Client()
        teacher_client.force_login(teacher_extra.user)
        dash_resp = teacher_client.get('/teacher-dashboard')
        self.assertEqual(dash_resp.status_code, 200)
        self.assertContains(dash_resp, '35000')

        # 5. Admin updates teacher WITHOUT changing password (password field left blank)
        upd_resp = admin_client.post(f'/update-teacher/{teacher_extra.id}', {
            'first_name': 'Janet',
            'last_name': 'Prof',
            'username': 'janeteacher',
            'password': '',  # left blank
            'salary': 40000,
            'mobile': '1122334455'
        })
        self.assertRedirects(upd_resp, '/admin-view-teacher')
        teacher_extra.refresh_from_db()
        self.assertEqual(teacher_extra.salary, 40000)
        self.assertEqual(teacher_extra.user.first_name, 'Janet')

        # Check teacher can still log in with original password
        teacher_client.logout()
        chk_login = teacher_client.post('/teacherlogin', {
            'username': 'janeteacher',
            'password': 'TeacherPass123!'
        }, follow=True)
        self.assertEqual(chk_login.status_code, 200)
        self.assertTrue(chk_login.context['user'].is_authenticated)

    def test_student_workflow_and_attendance(self):
        # 1. Student takes admission
        resp = self.client.post('/studentsignup', {
            'first_name': 'Alex',
            'last_name': 'Student',
            'username': 'alexstudent',
            'password': 'StudentPass123!',
            'roll': '101',
            'cl': 'one',
            'mobile': '1234567890',
            'fee': 5000
        })
        self.assertRedirects(resp, '/studentlogin')

        # 2. Admin approves student
        admin_user = User.objects.create_user('admin3', 'a@a.com', 'pass')
        self.admin_group.user_set.add(admin_user)
        admin_client = Client()
        admin_client.force_login(admin_user)

        student_extra = models.StudentExtra.objects.get(user__username='alexstudent')
        self.assertFalse(student_extra.status)
        admin_client.get(f'/approve-student/{student_extra.id}')
        student_extra.refresh_from_db()
        self.assertTrue(student_extra.status)

        # 3. Admin takes attendance for class 'one'
        att_post = admin_client.post('/admin-take-attendance/one', {
            'date': '2026-10-12',
            'present_status': ['Present']
        })
        self.assertRedirects(att_post, '/admin-attendance')

        # Verify Attendance record
        att_rec = models.Attendance.objects.get(roll='101', cl='one', date='2026-10-12')
        self.assertEqual(att_rec.present_status, 'Present')

        # 4. Retake attendance (updates existing instead of duplicating)
        admin_client.post('/admin-take-attendance/one', {
            'date': '2026-10-12',
            'present_status': ['Absent']
        })
        self.assertEqual(models.Attendance.objects.filter(roll='101', cl='one', date='2026-10-12').count(), 1)
        att_rec.refresh_from_db()
        self.assertEqual(att_rec.present_status, 'Absent')

        # 5. Student views own attendance
        student_client = Client()
        student_client.force_login(student_extra.user)
        att_view = student_client.post('/student-attendance', {
            'date': '2026-10-12'
        })
        self.assertEqual(att_view.status_code, 200)
        self.assertContains(att_view, 'Absent')

        # 6. Admin updates student without changing password
        upd_resp = admin_client.post(f'/update-student/{student_extra.id}', {
            'first_name': 'Alexander',
            'last_name': 'Student',
            'username': 'alexstudent',
            'password': '',
            'roll': '101',
            'cl': 'one',
            'mobile': '9988776655',
            'fee': 5500
        })
        self.assertRedirects(upd_resp, '/admin-view-student')
        student_extra.refresh_from_db()
        self.assertEqual(student_extra.fee, 5500)
        self.assertEqual(student_extra.user.first_name, 'Alexander')

    def test_notice_workflow(self):
        admin_user = User.objects.create_user('admin4', 'a@a.com', 'pass', first_name='Headmaster')
        self.admin_group.user_set.add(admin_user)
        admin_client = Client()
        admin_client.force_login(admin_user)

        resp = admin_client.post('/admin-notice', {'message': 'Sports Day on Friday'})
        self.assertRedirects(resp, '/admin-dashboard')

        notice = models.Notice.objects.first()
        self.assertIsNotNone(notice)
        self.assertEqual(notice.message, 'Sports Day on Friday')
        self.assertEqual(notice.by, 'Headmaster')

    def test_logout(self):
        user = User.objects.create_user('anyuser', 'u@u.com', 'pass')
        self.client.force_login(user)
        resp = self.client.get('/logout')
        self.assertRedirects(resp, '/')
        r = self.client.get('/admin-dashboard')
        self.assertRedirects(r, '/adminlogin?next=/admin-dashboard')

    def test_delete_teacher_and_student(self):
        admin_user = User.objects.create_user('admin5', 'a@a.com', 'pass')
        self.admin_group.user_set.add(admin_user)
        admin_client = Client()
        admin_client.force_login(admin_user)

        # Teacher delete
        t_user = User.objects.create_user('del_t', 't@t.com', 'pass')
        self.teacher_group.user_set.add(t_user)
        t_extra = models.TeacherExtra.objects.create(user=t_user, salary=1000, mobile='123', status=True)

        resp = admin_client.get(f'/delete-teacher-from-school/{t_extra.id}')
        self.assertRedirects(resp, '/admin-view-teacher')
        self.assertFalse(User.objects.filter(id=t_user.id).exists())
        self.assertFalse(models.TeacherExtra.objects.filter(id=t_extra.id).exists())

        # Student delete
        s_user = User.objects.create_user('del_s', 's@s.com', 'pass')
        self.student_group.user_set.add(s_user)
        s_extra = models.StudentExtra.objects.create(user=s_user, roll='999', cl='one', mobile='123', status=True)

        resp2 = admin_client.get(f'/delete-student-from-school/{s_extra.id}')
        self.assertRedirects(resp2, '/admin-view-student')
        self.assertFalse(User.objects.filter(id=s_user.id).exists())
        self.assertFalse(models.StudentExtra.objects.filter(id=s_extra.id).exists())

