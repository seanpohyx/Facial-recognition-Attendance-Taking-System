from flask_wtf import FlaskForm 
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField
from wtforms.validators import InputRequired, Email, Length, DataRequired, EqualTo

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=16)])
    remember = BooleanField('Remember me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    employeeNo = StringField('Employee Number', validators=[InputRequired(), Length(max=16)])
    name = StringField('Name', validators=[InputRequired(), Length(max=80)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=8, max=16)])
    confirmPassword = PasswordField('Confirm Password', validators=[InputRequired(), Length(min=8, max=16)])
    appointment = SelectField('Appointment', choices=[('Prof','Professor') , ('Labtech','Lab Technician')])
    submit = SubmitField('Register')

class UpdateForm(FlaskForm):
    password = PasswordField('Old Password', validators=[InputRequired(), Length(min=8, max=16)])
    newPassword = PasswordField('New Password', validators=[InputRequired(), Length(min=8, max=16)])
    confirmPassword = PasswordField('Confirm Password', validators=[InputRequired(), Length(min=8, max=16)])
    submit = SubmitField('Update Password')

class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    newPassword = PasswordField('New Password', validators=[InputRequired(), Length(min=8, max=16)])
    confirmPassword = PasswordField('Confirm Password', validators=[InputRequired(), Length(min=8, max=16)])
    submit = SubmitField('Submit')

class manualAttendanceForm(FlaskForm):
    matric_no = StringField('matric', validators=[InputRequired(), Length(max=10)], render_kw={"placeholder": "U1234567A"})
    submit = SubmitField('Confirm')

class searchForm(FlaskForm):
    search = StringField('searchBar', validators=[ Length(max=50)], render_kw={"placeholder": "Enter search"})
    submit = SubmitField('Search')

class confirmForm(FlaskForm):
    submit = SubmitField('Confirm')
    
class uploadTimetableForm(FlaskForm):
    fileInput = FileField('Please upload timetable with (.CSV) format', validators=[FileRequired(), FileAllowed(['csv'], 'CSV file only !')])
    submit = SubmitField('Submit')

class closeForm(FlaskForm):
    submit = SubmitField('Submit')
    
