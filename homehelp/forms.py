from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField,SubmitField,PasswordField,EmailField,SelectField,FileField,BooleanField,IntegerField,RadioField
from wtforms.validators import DataRequired,Email, Length,InputRequired
from  homehelp.models import db, Category


class LoginForm(FlaskForm):
    email = EmailField('Email', validators=[Email(message='Enter Email')]) #<label>Title</label><input type='text'>
    password = PasswordField('Password', validators=[DataRequired(message='Password cannot be empty')])
    submit = SubmitField('Login')

class HelpLoginForm(FlaskForm):
    email = EmailField('Email', validators=[Email(message='Enter Email')]) #<label>Title</label><input type='text'>
    password = PasswordField('Password', validators=[DataRequired(message='Password cannot be empty')])
    submit = SubmitField('Login')

class AdminLoginForm(FlaskForm):
    email = EmailField('Email', validators=[Email(message='Enter Email')]) #<label>Title</label><input type='text'>
    password = PasswordField('Password', validators=[DataRequired(message='Password cannot be empty')])
    submit = SubmitField('Login')


class SigninForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    gender = SelectField('Gender', choices=[('','Select Gender'),('male','Male'),('female','Female'),('others','Others')],validators=[InputRequired()])
    phone = IntegerField('Phone Number', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, max=100)])
    cpassword = PasswordField('Password', validators=[DataRequired()])
    state = SelectField('State', choices=[(0,'Select your state'),(1, 'Abia State'), (2, 'Adamawa State'),
                                          (3, 'Akwa Ibom State'),
                                          (4, 'Anambra State'),
                                          (5, 'Bauchi State'),
                                          (6, 'Bayelsa State'),
                                          (7, 'Benue State'),
                                          (8, 'Borno State'),
                                          (9, 'Cross River State'),
                                          (10, 'Delta State'),
                                          (11, 'Ebonyi State'),
                                          (12, 'Edo State'),
                                          (13, 'Ekiti State'),
                                          (14, 'Enugu State'),
                                          (15, 'FCT'),
                                          (16, 'Gombe State'),
                                          (17, 'Imo State'),
                                          (18, 'Jigawa State'),
                                          (19, 'Kaduna State'),
                                          (20, 'Kano State'),
                                          (21, 'Katsina State'),
                                          (22, 'Kebbi State'),
                                          (23, 'Kogi State'),
                                          (24, 'Kwara State'),
                                          (25, 'Lagos State'),
                                          (26, 'Nasarawa State'),
                                          (27, 'Niger State'),
                                          (28, 'Ogun State'),
                                          (29, 'Ondo State'),
                                          (30, 'Osun State'),
                                          (31, 'Oyo State'),
                                          (32, 'Plateau State'),
                                          (33, 'Rivers State'),
                                          (34, 'Sokoto State'),
                                          (35, 'Taraba State'),
                                          (36, 'Yobe State'),
                                          (37, 'Zamfara State')],
                          # ensures the value submitted is an integer (ID)
                        validators=[DataRequired(message="State is required")])
    #image = FileField('Image', validators=[DataRequired()])
    send = SubmitField('Create Account')


class HelpSigninForm(FlaskForm):
    fname = StringField('Name', validators=[DataRequired(message='Enter your first name')])
    lname = StringField('Name', validators=[DataRequired(message='Enter your last name')])
    email = EmailField('Email', validators=[Email(message='Enter Email')])
    phone = StringField('Phone', validators=[DataRequired(message='Enter your phone number')])
    price = StringField('Price', validators=[DataRequired(message='Set your price')])
    password = PasswordField('Password', validators=[DataRequired(message='Password cannot be empty')])
    cpassword = PasswordField('Password', validators=[DataRequired(message='Password cannot be empty')])
    # check = BooleanField('check')
    address = TextAreaField('Description', validators=[DataRequired(message='Address cannot be empty')])
    send = SubmitField('Create Account')
    image = FileField("Image", validators=[FileAllowed(['jpg','jpeg','png','gif'],'Images only')])
    category = SelectField('Category', choices=[], validators=[DataRequired()])
    
    state = SelectField('State', choices=[(0,'Select your state'),(1, 'Abia State'), (2, 'Adamawa State'),
                                          (3, 'Akwa Ibom State'),
                                          (4, 'Anambra State'),
                                          (5, 'Bauchi State'),
                                          (6, 'Bayelsa State'),
                                          (7, 'Benue State'),
                                          (8, 'Borno State'),
                                          (9, 'Cross River State'),
                                          (10, 'Delta State'),
                                          (11, 'Ebonyi State'),
                                          (12, 'Edo State'),
                                          (13, 'Ekiti State'),
                                          (14, 'Enugu State'),
                                          (15, 'FCT'),
                                          (16, 'Gombe State'),
                                          (17, 'Imo State'),
                                          (18, 'Jigawa State'),
                                          (19, 'Kaduna State'),
                                          (20, 'Kano State'),
                                          (21, 'Katsina State'),
                                          (22, 'Kebbi State'),
                                          (23, 'Kogi State'),
                                          (24, 'Kwara State'),
                                          (25, 'Lagos State'),
                                          (26, 'Nasarawa State'),
                                          (27, 'Niger State'),
                                          (28, 'Ogun State'),
                                          (29, 'Ondo State'),
                                          (30, 'Osun State'),
                                          (31, 'Oyo State'),
                                          (32, 'Plateau State'),
                                          (33, 'Rivers State'),
                                          (34, 'Sokoto State'),
                                          (35, 'Taraba State'),
                                          (36, 'Yobe State'),
                                          (37, 'Zamfara State')],
                          # ensures the value submitted is an integer (ID)
                        validators=[DataRequired(message="State is required")])
    
    


class AdminSigninForm(FlaskForm):
    username = StringField('Name', validators=[DataRequired(message='Enter your name')])
    email = EmailField('Email', validators=[Email(message='Enter Email')])
    password = PasswordField('Password', validators=[DataRequired(message='Password cannot be empty')])



    


