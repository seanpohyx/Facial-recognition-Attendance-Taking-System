from flask import Flask, render_template, url_for, Response, request, redirect, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
import values, csv, io
import facial_recognition
from forms import LoginForm, RegistrationForm, UpdateForm, ForgotPasswordForm,\
    ResetPasswordForm, manualAttendanceForm, searchForm, confirmForm, uploadTimetableForm, closeForm
from models import Users, Attend, Classes, Staffs, Students, db, app, mail
from flask_mail import Message
from datetime import datetime
from collections import defaultdict

@app.route("/", methods=['GET', 'POST'])
@app.route("/index", methods=['GET', 'POST'])
def index():
    form = LoginForm()
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if form.validate_on_submit():
        user = Users.query.filter_by(email=(form.email.data).casefold()).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))

        flash('Invalid username or password', 'danger')

    return render_template('index.html', form=form, title="login")

@app.route("/registrationForm", methods=['GET', 'POST'])
@login_required
def registrationForm():    

    if not current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        email = (form.email.data).casefold()
        emailValidation = email.split("@")
        employeeNo = (form.employeeNo.data).casefold()
        name = form.name.data
        password = form.password.data
        confirmPassword = form.confirmPassword.data
        role = form.appointment.data

        status = Users.query.filter_by(email=email).first()
        if (status): 
            flash("An existing account already exist in database", 'warning')
            return redirect(url_for('registrationForm'))

        if (password != confirmPassword):
            flash("Passwords do not match", 'warning')
            return redirect(url_for('registrationForm'))

        if (emailValidation[1] != 'e.ntu.edu.sg'):
            flash("Please register using NTU email", 'warning')
            return redirect(url_for('registrationForm'))
        
        hash_value = generate_password_hash(confirmPassword)

        newUser = Users(email=email,password=hash_value,type="staff")
        db.session.add(newUser)
        db.session.commit()
        userId = newUser.serialize()
        newStaff = Staffs(name=name,employeeNo=employeeNo,role=role,userId=userId['id'])
        db.session.add(newStaff)
        db.session.commit()

        flash('An account has been created.', 'info')
        return redirect(url_for('index'))

    return render_template('registrationForm.html', form=form, title="register")

@app.route("/updatePassword", methods=['GET', 'POST'])
@login_required
def updatePassword():
    
    if not current_user.is_authenticated:
        return redirect(url_for('index'))
        
    form = UpdateForm()
    if current_user.is_authenticated:
        g.user = current_user.get_id()
        oldPassword = form.password.data
        newPassword = form.newPassword.data
        confirmPassword = form.confirmPassword.data

        if form.validate_on_submit():
            user = Users.query.filter_by(id=g.user).first()
            if user:
                if check_password_hash(user.password, oldPassword):
                    if (newPassword != confirmPassword):
                        flash("Passwords do not match", 'warning')
                    else:
                        hash_value = generate_password_hash(confirmPassword)
                        user = Users.query.get(g.user)
                        user.password = hash_value
                        db.session.commit()
                        flash("Password updated", 'info')
                        return redirect(url_for('index'))
                else: 
                    flash("Wrong password", 'warning')


    dashboard_data = values.dashboards['admin'] if current_user.type == 'admin' else values.dashboards['staffs']
    return render_template('updatePassword.html', form=form, title="update password", dashboards=dashboard_data, len=len(dashboard_data))


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender='Administrator@FATS.com', recipients=[user.email])
    msg.body = f'''Click link to reset password:
{url_for('resetPassword', token=token, _external=True)}

If you did not make this request, please contact NTU System Administrator.

Thank you.

Regards
FATS SYSTEM
'''
    mail.send(msg)

@app.route("/forgotPassword", methods=['GET', 'POST'])
def forgotPassword():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=(form.email.data).casefold()).first()
        if user is None:
            flash('Email does not exist', 'warning')
            return redirect(url_for('index'))
        send_reset_email(user)
        flash('An email has been sent for further instructions', 'info')
        return redirect(url_for('index'))
    return render_template('forgotPassword.html', form=form, title="Forgot Password")

@app.route("/resetPassword/<token>", methods=['GET', 'POST'])
def resetPassword(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    user = Users.verify_reset_token(token)
    if user is None:
        flash('Token expired or invalid', 'warning')
        return redirect(url_for('index'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        newPassword = form.newPassword.data
        confirmPassword = form.confirmPassword.data

        if (newPassword != confirmPassword):
            flash("Passwords do not match", 'warning')
        
        hash_value = generate_password_hash(confirmPassword)
        user.password = hash_value
        db.session.commit()
        flash('Password has been updated', 'info')
        return redirect(url_for('index'))
        
    return render_template('resetPassword.html', form=form, title="Reset Password")

def findUser(userId,selection):
    if(selection == 1):
        staff = Staffs.query.filter_by(employeeNo=userId).first()
        return staff.id
    else:
        student = Students.query.filter_by(matricNo=userId).first()
        return student.id

def findClass(moduleName, className):
    classId = Classes.query.filter_by(moduleCode=moduleName,classCode=className).first()
    return classId.id

@app.route("/uploadTimetableProf", methods=['GET','POST'])
@login_required
def TTP():
    if not current_user.is_authenticated:
        return redirect(url_for('index'))

    form = uploadTimetableForm()
    if form.validate_on_submit():
        f = form.fileInput.data
        fstring = f.read()
        convertfstring = str(fstring,encoding='utf-8')
        csv_dicts = [{k: v for k, v in row.items()} for row in csv.DictReader(convertfstring.splitlines(), skipinitialspace=True)]
        for x in csv_dicts:
            try:
                staffId = findUser(x['staffId'],1)
                if not staffId is None:
                    Class = Classes(module=x['module'],day=x['day'],startTime=x['startTime'],staffInCharged=staffId,duration=x['duration'],frequency=x['frequency'],moduleCode=x['moduleCode'],classCode=x['classCode'])
                    db.session.add(Class)
                    db.session.commit()
                    flash("Upload Successful",'info')
            except:
                flash('CSV contains incorrect fields.', 'danger')
        
    return render_template('uploadTimetableProf.html', form=form, title="Upload")

@app.route("/uploadTimetableStudent", methods=['GET','POST'])
@login_required
def TTS():
    if not current_user.is_authenticated:
        return redirect(url_for('index'))

    form = uploadTimetableForm()
    if form.validate_on_submit():
        f = form.fileInput.data
        fstring = f.read()
        convertfstring = str(fstring,encoding='utf-8')
        csv_dicts = [{k: v for k, v in row.items()} for row in csv.DictReader(convertfstring.splitlines(), skipinitialspace=True)]
        for x in csv_dicts:
            try:
                studentId = findUser(x['studentId'],0)
                classId = findClass(x['moduleCode'],x['classCode'])
                if not studentId is None:
                    if not classId is None:
                        Class = Attend(classId=classId,studentId=studentId,attendance="false")
                        db.session.add(Class)
                        db.session.commit()
                        flash("Upload Successful",'info')
            except:
                flash('CSV contains incorrect fields.', 'danger')

    return render_template('uploadTimetableStudent.html', form=form, title="Upload")

@app.route("/dashboard")
@login_required
def dashboard():
    dashboard_data = values.dashboards['admin'] if current_user.type == 'admin' else values.dashboards['staffs']
    return render_template('dashboard.html', dashboards=dashboard_data, len=len(dashboard_data))

@app.route("/students-records", methods=['GET', 'POST'])
@login_required
def students_records():

    dashboard_data = values.dashboards['admin'] if current_user.type == 'admin' else values.dashboards['staffs']
    students_data = Students.query.all()

    searchform = searchForm()

    if searchform.validate_on_submit():
        search_results = "%{}%".format(request.form.get('search'))
        if search_results is '':
            students_data = Students.query.all()
        else:
            students_data = Students.query.filter(Students.name.ilike(search_results)).all()

        return render_template('students.html', dashboards=dashboard_data, len=len(dashboard_data),
                               searchform=searchform, students=students_data, showBtn=True)


    return render_template('students.html', dashboards=dashboard_data, len=len(dashboard_data),searchform=searchform,
                           students=students_data, showBtn=True)

@app.route("/my-classes", methods=['GET', 'POST'])
@login_required
def my_classes():

    dashboard_data = values.dashboards['admin'] if current_user.type == 'admin' else values.dashboards['staffs']
    staff_id = Staffs.query.filter_by(userId=current_user.id).first_or_404().id
    classes_data = Classes.query.filter_by(staffInCharged=staff_id)
    form = searchForm()

    print(dashboard_data)
    if form.validate_on_submit():
        search_results = "%{}%".format(request.form.get('search'))
        if search_results is '':
            classes_data = Classes.query.filter_by(staffInCharged=staff_id)
        else:
            classes_data = Classes.query.filter_by(staffInCharged=staff_id) \
                .filter(Classes.module.ilike(search_results)).all()

        return render_template('classes.html', dashboards=dashboard_data, len=len(dashboard_data),
                               form=form, classes=classes_data)


    return render_template('classes.html', dashboards=dashboard_data, len=len(dashboard_data),
                               form=form, classes=classes_data)

def send_absentee_email(email,lesson):
    moduleName = lesson.module
    moduleCode = lesson.moduleCode
    moduleGroup = lesson.classCode
    moduleDay = lesson.day
    moduleTime = lesson.startTime
    msg = Message('Attendance warning' , sender='Administrator@FATS.com', recipients=[email])
    msg.body = f'''Dear Student, 
    
Please be informed that you have missed the follow lesson
Class: {moduleCode} -  {moduleName} 
Group: {moduleGroup}
Time: {moduleDay} @ {moduleTime}

If there are any mistakes made by the system, please inform your tutor.

Thank you.

Regards
FATS SYSTEM
'''
    mail.send(msg)

@app.route("/sendAbsenteeEmail/<int:class_id>", methods=['GET', 'POST'])
@login_required
def sendAbsenteeEmail(class_id):
  
    students_data = db.session.query(Students, Attend) \
        .filter(Attend.studentId == Students.id) \
        .filter(Attend.classId == class_id).all()

    searchform = searchForm()
    manualForm = manualAttendanceForm()
    sendAbsenteeEmail = confirmForm()
    closeAttendance = closeForm()
    
    if sendAbsenteeEmail.validate_on_submit():
        for x in students_data:
            print(x)
            attendanceStatus = x[1].attendance
            attendanceClose = x[1].closedate
            if not attendanceClose: #Attendance not closed yet
                if not attendanceStatus: #Attendance is false
                    studentEmail = x[0].email
                    lessonId = x[1].classId
                    lesson = Classes.query.filter_by(id=lessonId).first()
                    send_absentee_email(studentEmail,lesson)

        flash('Email Sent!','success')
        return redirect(url_for('class_students',class_id=class_id))

    return render_template('students.html', dashboards=values.dashboards['staffs'], closeAttendance=closeAttendance, sendAbsenteeEmail=sendAbsenteeEmail, manualForm=manualForm, searchform=searchform,
                           len=len(values.dashboards['staffs']), students=students_data, classId=class_id)

@app.route("/class-students/<int:class_id>", methods=['GET', 'POST'])
@login_required
def class_students(class_id):

    students_data = db.session.query(Students, Attend) \
        .filter(Attend.studentId == Students.id) \
        .filter(Attend.classId == class_id) \
        .filter(Attend.closedate == None).all()

    searchform = searchForm()
    manualForm = manualAttendanceForm()
    sendAbsenteeEmail = confirmForm()
    closeAttendance = closeForm()

    if searchform.validate_on_submit():
        search_results = "%{}%".format(request.form.get('search'))
        if search_results is '':
            students_data = db.session.query(Students, Attend) \
                .filter(Attend.studentId == Students.id) \
                .filter(Attend.classId == class_id) \
                .filter(Attend.closedate == None).all()
        else:
            students_data = db.session.query(Students, Attend) \
                .filter(Attend.studentId == Students.id) \
                .filter(Attend.classId == class_id) \
                .filter(Attend.closedate == None) \
                .filter(Students.name.ilike(search_results)).all()
            flash("Searched", 'info')

    return render_template('students.html', dashboards=values.dashboards['staffs'], closeAttendance=closeAttendance, sendAbsenteeEmail=sendAbsenteeEmail, manualForm=manualForm, searchform=searchform,
                           len=len(values.dashboards['staffs']), students=students_data, classId=class_id)

@app.route("/manual-insert/<int:class_id>", methods=['GET', 'POST'])
@login_required
def manualInsert(class_id):

    students_data = db.session.query(Students, Attend) \
        .filter(Attend.studentId == Students.id) \
        .filter(Attend.classId == class_id) \
        .filter(Attend.closedate == None).all()

    searchform = searchForm()
    manualForm = manualAttendanceForm()
    sendAbsenteeEmail = confirmForm()
    closeAttendance = closeForm()
    
    if manualForm.validate_on_submit():
        student_attendance = Attend.query \
            .join(Students, Attend.studentId == Students.id) \
            .filter(Students.matricNo == request.form.get('matric_no').upper()) \
            .filter(Attend.classId == class_id) \
            .filter(Attend.closedate == None).first()

        if student_attendance is not None:
            student_attendance.attendance = True
            student_attendance.datetime = datetime.now()
            db.session.commit()

            students_data = db.session.query(Students, Attend) \
            .filter(Attend.studentId == Students.id) \
            .filter(Attend.classId == class_id) \
            .filter(Attend.closedate == None).all()

            flash('Your attendance has been updated!', 'success')
            return redirect(url_for('class_students',class_id=class_id))

    return render_template('students.html', dashboards=values.dashboards['staffs'], closeAttendance=closeAttendance, sendAbsenteeEmail=sendAbsenteeEmail, manualForm=manualForm, searchform=searchform,
                           len=len(values.dashboards['staffs']), students=students_data, classId=class_id)


@app.route("/close-attendance/<int:class_id>", methods=['GET', 'POST'])
@login_required
def closeAttendance(class_id):
  
    students_data = db.session.query(Students, Attend) \
        .filter(Attend.studentId == Students.id) \
        .filter(Attend.classId == class_id) \
        .filter(Attend.closedate == None).all()

    closeAttendance = closeForm()
    
    if closeAttendance.validate_on_submit():
        flash("Attendance Session Closed" , "success")

        for student in students_data:
            attendanceIdentifierDigit = student[1].id
            classIdentifierDigit = student[1].classId
            studentIdentifierDigit = student[1].studentId
            new_attend = Attend(classId=classIdentifierDigit, studentId=studentIdentifierDigit, attendance='false')
            db.session.add(new_attend)
            query = Attend.query.filter_by(id=attendanceIdentifierDigit).first()
            query.closedate = datetime.now()
            db.session.commit()
        return redirect(url_for('class_students',class_id=class_id))

    # return render_template('students.html', dashboards=values.dashboards['staffs'], closeAttendance=closeAttendance, sendAbsenteeEmail=sendAbsenteeEmail, manualForm=manualForm, searchform=searchform,
    #                        len=len(values.dashboards['staffs']), students=students_data, classId=class_id)

@app.route("/view-report/<int:class_id>", methods=['GET', 'POST'])
@login_required
def view_report(class_id):

    try:
        report_data = db.session.query(Students, Attend) \
        .filter(Attend.studentId == Students.id) \
        .filter(Attend.classId == class_id) \
        .filter(Attend.closedate != None).all()

        groups = defaultdict(list)

        for x in report_data:
            date = x[1].closedate.date()
            timestampStr = date.strftime("%d-%b-%Y")
            groups[timestampStr].append(x)
            sortedList = groups.values()

        yeet = list(sortedList)

    except:
        flash("No report available", 'info')
        return redirect(url_for('index'))

    return render_template('viewReport.html', dashboards=values.dashboards['staffs'],len=len(values.dashboards['staffs']), reports=yeet, classId=class_id)

@app.route("/mark-attendance/<int:class_id>", methods=['GET', 'POST'])
@login_required
def markAttendance(class_id):

    # students_data = Students.query\
    #     .join(Attend, Attend.studentId == Students.id)\
    #     .filter(Attend.classId == class_id)
    return render_template('markAttendance.html', dashboards=values.dashboards['staffs'],
                           len=len(values.dashboards['staffs']), classId=class_id)

@app.route("/register-student/<int:student_id>", methods=['GET', 'POST'])
def registerStudent(student_id):
    student_record = Students.query.get_or_404(student_id)

    form = confirmForm()
    if form.validate_on_submit():
        return redirect(url_for('dashboard'))

    return render_template('registerFace.html', dashboards=values.dashboards['admin'], form=form,
                           len=len(values.dashboards['admin']), student=student_record)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

#classify data
# @app.route("/classifier")
# def classifer():
#     return facial_recognition.train_classifer(Students)

# this route is to generate video for streaming
@app.route("/register_new_face/<int:student_id>", methods=['GET', 'POST'])
def register_new_face(student_id):
    student = Students.query.get_or_404(student_id)
    return Response(facial_recognition.registerFaceCam(student, Students), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/attendance_video/<int:class_id>', methods=['GET', 'POST'])
def attendance_video(class_id):
    students_data = db.session.query(Students, Attend) \
        .filter(Attend.studentId == Students.id) \
        .filter(Attend.classId == class_id) \
        .filter(Attend.closedate == None).all()
    return Response(facial_recognition.markAttendanceCam(students_data, Attend, db.session), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(debug=True, threaded=True)
