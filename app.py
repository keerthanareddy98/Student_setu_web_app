from email import message
from random import randint
from flask import Flask,flash, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from werkzeug.security import check_password_hash, generate_password_hash
import MySQLdb.cursors
import re
from datetime import datetime
from helper import login_required
from sendemail import sendgridmail

replyto=0
ideano=0
forgotten_user_email=""
verifyotp=0
app = Flask(__name__)
app.secret_key = 'a'

#app.config['MYSQL_HOST'] = "localhost"
#app.config['MYSQL_USER'] = "root"
#app.config['MYSQL_PASSWORD'] = ""
#app.config['MYSQL_DB'] = "users"


#DB details
app.config['MYSQL_HOST'] = 'remotemysql.com'
app.config['MYSQL_USER'] = 'BfCGjdLClZ'
app.config['MYSQL_PASSWORD'] = "ht4lTbpV6q"
app.config['MYSQL_DB'] = 'BfCGjdLClZ'
mysql = MySQL(app)

#main page(root)
@app.route('/', methods = ['GET'])
def index():
    return render_template("index.html")


#register page for students and faculty
@app.route('/register', methods =['POST', 'GET'])
def register():
    if request.method == 'POST' :
        regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'  
        name = request.form['name']
        user=request.form['user']
        useridno =request.form['useridno']
        email = request.form['email']
        phone = request.form['phone']
        dept = request.form.get('dept')
        year=request.form['year']
        dept+=" "+year
        gender= request.form.get('gender')
        password = request.form['password']
        confirmPassword = request.form['confirmpassword']
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM details WHERE email = % s', (email, ))  
        e=cursor.fetchall()
        cursor.execute('SELECT * FROM details WHERE useridno = % s', (useridno, ))  
        account = cursor.fetchall()
        if not re.match(r'[A-Za-z]+', name):
            flash("Name must contain only characters!")
        elif account:
            flash("User already exists")
        elif(e):
            flash("Email already exists")

        elif not (re.match(regex,email)):
            flash("Invalid email address !")
        elif not re.match(r'[0-9]+', phone):
            flash("Phone no. must contain only numbers!")
        elif confirmPassword!=password:
            flash("Passwords does not match")
        else:
            password=generate_password_hash(password)
            TEXT = "Hello "+name + ",\n\n"+ """You are successfully registered""" 
            TEXT+="{}\n\n".format("""Welcome..""")
            message  = 'Subject: {}\n\n{}'.format("COMPLAINT BOX", TEXT)
            x=sendgridmail(email,TEXT)
            if x==1: 
                flash("You have successfully registered on COMPLAINT BOX")
                if(user=="Student"):
                    cursor.execute('INSERT INTO details VALUES (NULL, % s, % s, % s,% s, %s, %s, %s, %s)', ('Student', name, useridno, email, phone, dept, gender, password))
                else:
                    cursor.execute('INSERT INTO details VALUES (NULL, % s, % s, % s,% s, %s, %s, %s, %s)', ('Faculty', name, useridno, email, phone, dept, gender, password))
                mysql.connection.commit()
            else:
                flash("Oops..! Your registration failed")
            return redirect("/")
    return render_template("register.html")

#student menu when student logs in
@app.route('/studentmenu', methods=['GET', 'POST'])
@login_required
def studentmenu():
    global userid
    return render_template("studentmenu.html")

#faculty menu when student logs in
@app.route('/facultymenu', methods=['GET', 'POST'])
@login_required
def facultymenu():
    global userid
    return render_template("facultymenu.html")


#login page for students and faculty
@app.route('/login', methods=['GET', 'POST'])
def login():
    global userid
    if request.method == 'POST' :
        user=request.form['user']
        useridno = request.form['useridno']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM details WHERE useridno = % s', (useridno, ))
        account = cursor.fetchone() 
        if account and account[1]==user:
            print(account)
            session['loggedin'] = True
            session['user_id'] = account[3]
            userid =  account[3]
            session['name'] = account[2] 
            pd=account[8]
            if check_password_hash(pd,password):
                session['loggedin'] = True
                session['user_id'] = account[3]
                userid =  account[3]
                session['name'] = account[2]
                if(user=="Student"):
                    session['student'] = True
                    return redirect("/studentmenu")
                else:
                    session['faculty'] = True
                    return redirect("/facultymenu")
        else:
            flash("User does not exists")
    return render_template("login.html")


#student asking questions 
@app.route('/askquestion', methods=['GET', 'POST'])
@login_required
def askquestion():
    if request.method == 'POST' :
        userid = session["user_id"]
        anony = request.form['anonymous']
        check = request.form.get("notify") != None
        qns = request.form['qns']
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM details WHERE useridno = % s', (userid, ))
        account = cursor.fetchone()  
        print(account)
        today=datetime.now()  
        an=1 if (anony=="yes") else 0
        cursor.execute('INSERT INTO ciq_details VALUES (NULL, % s, % s, % s,% s, %s, %s, %s, %s, %s, 1)', (account[3], account[2], account[6], 'q', qns, "none", an, check, today))
        mysql.connection.commit()
        flash("Question posted")
        return redirect("/studentmenu")
    return render_template("askquestion.html")

#student giving complaints
@app.route('/complaint', methods=['GET', 'POST'])
@login_required
def complaint():
    if request.method == 'POST' :
        userid = session["user_id"]
        anony = request.form['anonymous']
        check = request.form.get("notify") != None
        comp = request.form['comp']
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM details WHERE useridno = % s', (userid, ))
        account = cursor.fetchone()  
        print(account)
        today=datetime.now()  
        an=1 if (anony=="yes") else 0
        cursor.execute('INSERT INTO ciq_details VALUES (NULL, % s, % s, % s,% s, %s, %s, %s, %s, %s, 1)', (account[3], account[2], account[6], 'c', comp, "none", an, check, today))
        mysql.connection.commit()
        flash("Complaint generated")
        return redirect("/")
    return render_template("complaint.html")


#student proposing their idea
@app.route('/idea', methods=['GET', 'POST'])
@login_required
def idea():
    if request.method == 'POST' :
        userid = session["user_id"]
        anony = request.form['anonymous']
        check = request.form.get("notify") != None
        idea = request.form['idea']
        benefit=request.form['benefit']
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM details WHERE useridno = % s', (userid, ))
        account = cursor.fetchone()  
        print(account)
        today=datetime.now()  
        an=1 if (anony=="yes") else 0
        cursor.execute('INSERT INTO ciq_details VALUES (NULL, % s, % s, % s,% s, %s, %s, %s, %s, %s, 1)', (account[3], account[2], account[6], 'i', idea, benefit, an, check, today))
        mysql.connection.commit()
        flash("Ideas is proposed")
        return redirect("/")
    return render_template("idea.html")



#list for faculty to view students questions
@app.route('/faculty_question', methods = ['GET'])
@login_required
def faculty_question():
    session['latest'] = True
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM ciq_details WHERE status=%s AND ciq_flag=%s", (1,'q',))
    mysql.connection.commit()
    rows=cur.fetchall()
    return render_template("faculty_question.html", records = rows)
  

#list for faculty to view students complaints
@app.route('/faculty_complaint', methods = ['GET'])
@login_required
def faculty_complaint():
    session['latest'] = True
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM ciq_details WHERE status=%s AND ciq_flag=%s", (1,'c',))
    mysql.connection.commit()
    rows=cur.fetchall()
    return render_template("faculty_complaint.html", records = rows)
  
#list for faculty to view students ideas
@app.route('/faculty_idea', methods = ['GET'])
@login_required
def faculty_idea():
    session['latest'] = True
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM ciq_details WHERE status=%s AND ciq_flag=%s", (1,'i',))
    mysql.connection.commit()
    rows=cur.fetchall()
    return render_template("faculty_idea.html", records = rows)


    
#forgot page to enter email and otp to modify
@app.route('/forgotpage', methods=['GET', 'POST'])
def forgotpage():
    return render_template("forgotpage.html")


#sending otp to provided mail ID
@app.route("/sendotp", methods=['GET', 'POST'])    
def sendotp():
    global forgotten_user_email
    global verifyotp
    regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'  
    try:
        email=request.form["email"]
    except KeyError:
        flash("Enter email address !")
    if not (re.match(regex,email)):
        flash("Invalid email address !")
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM details WHERE email=%s", (email,))
    mysql.connection.commit()
    row=cur.fetchone()
    print(row)
    if(row is None):
        flash("Invalid User..!")
        print("noneeeeeeeeeeeeeeee")
    else:
        verifyotp=randint(1000, 9999)
        x=sendgridmail(email,str(verifyotp))
        if(x==1):
            flash("OTP sent..!")
        forgotten_user_email=row[4]
    

    #send mail for "forgotten_user_email" also generate & save the random number in a variable and make it global
    return render_template("forgotpage.html")

#veirfy user with OTP  before viewing page to change password
@app.route("/verify", methods=['GET', 'POST']) 
def verify():
    global verifyotp
    otp=request.form["otp"]
    print(otp,verifyotp)
    if(otp==str(verifyotp)):
        flash("OTP Verified..!")
        return render_template("verify.html")
    return render_template("forgotpage.html")
    
#page to change password
@app.route("/changepwd", methods=['GET', 'POST']) 
def changepwd():
    p1=request.form["newpassword"]
    p2=request.form["confirmpassword"]
    if(p1==p2):
        cur = mysql.connection.cursor()
        cur.execute("UPDATE details SET password=%s WHERE email=%s ", (generate_password_hash(p1),forgotten_user_email,))
        mysql.connection.commit()
        flash("Password changed successfully")
        return render_template("login.html")
    flash("Both password does not match")
    return render_template("verify.html")
    
#deleting row from ideas table {[...This should also be implemented for questions and complaints as well...]}
@app.route('/ignore/<string:dt>', methods = ['GET'])
@login_required
def ignore(dt):
    print(dt)
    flash("Record Has Been Deleted Successfully")
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM ciq_details WHERE sno=%s", (dt,))
    mysql.connection.commit()
    return redirect(url_for('facultymenu'))


#faculty giving reply for an idea
#here http://127.0.0.1:8080/faculty_idea/reply/1234/3 when i remove faculty_idea its working
#the same is repeating with viewed and latest, if u manually remove faculty_idea and all its showing!!!!!
@app.route('/reply/<string:dt>/<string:si>', methods = ['GET'])
@login_required
def reply(dt,si):
    global replyto
    global ideano
    ideano=si
    print("ideano issss:",dt,si)
    replyto=dt
    
    return render_template("reply.html")
    #return redirect(url_for('reply'))



#faculty giving reply for a complaint
@app.route('/complaint_reply/<string:dt>/<string:si>', methods = ['GET'])
@login_required
def complaint_reply(dt,si):
    global replyto
    global ideano
    ideano=si
    print("compno issss:",dt,si)
    replyto=dt

    return render_template("reply.html")
    #return redirect(url_for('complaint_reply'))

#faculty giving reply for a question
# @app.route('/question_reply/<string:dt>/<string:si>', methods = ['GET'])
# @login_required
# def question_reply(dt,si):
#     global replyto
#     global ideano
#     ideano=si
#     print("qns issss:",dt,si)
#     replyto=dt
#     return ""
#     # return render_template("reply.html")
#     #return redirect(url_for('question_reply'))


#faculty giving reply for an idea
@app.route('/replysent/<string:replyto>/<string:ideano>', methods =['GET', 'POST'])
@login_required
def replysent(replyto,ideano):
    if request.method == 'POST' :
        answer= request.form["answer"]
        print(replyto,ideano)
        cur = mysql.connection.cursor()
        cur.execute("SELECT name from details WHERE useridno=%s",(session['user_id'],))
        name=cur.fetchone()
        cur.execute("SELECT email from details WHERE useridno=%s",(replyto,))
        email=cur.fetchone()
        cur.execute("SELECT statement from ciq_details WHERE sno=%s",(ideano,))
        idea=cur.fetchone()
        print(idea)
        n=cur.execute("SELECT notify from ciq_details WHERE sno=%s",(ideano,))
        up=cur.execute("UPDATE ciq_details SET status=%s WHERE sno=%s ", (0,ideano,))
        print("keerthana : ",session['user_id'],answer)
        #tobeupdated=str([idea[0],name,answer])
        print(idea,name)
        cur.execute("SELECT ciq_flag from ciq_details WHERE sno=%s",(ideano,))
        flag=cur.fetchone()[0]
        print(flag)
        tobeupdated=idea[0]+"#$&$#"+name[0]+"#$&$#"+answer
        up=cur.execute("UPDATE ciq_details SET statement=%s WHERE sno=%s ", (tobeupdated,ideano,))
        if n:
            message="You have been received your response \n For the query: "+ idea[0] +"\n \n" + answer
            sendgridmail(email,message)
        mysql.connection.commit()
        print(up)
        flash("Reply has been sent Successfully")
        if(flag=='i'):
            #return render_template("faculty_idea.html")
            return redirect(url_for('faculty_idea'))
        elif(flag=='q'):
            return redirect(url_for('faculty_question'))
            # return render_template("faculty_question.html")
        else:
            return redirect(url_for('faculty_complaint'))
            # return render_template("faculty_complaint.html")

#faculty giving reply for an idea
@app.route('/editsentreply/<string:replyto>/<string:ideano>', methods =['GET', 'POST'])
@login_required
def editsentreply(replyto,ideano):
    if request.method == 'POST' :
        print(replyto,ideano)
        answer= request.form["answer"]

        cur = mysql.connection.cursor()
        # cur.execute("SELECT name from details WHERE useridno=%s",(session['user_id'],))
        # name=cur.fetchone()
        # cur.execute("SELECT email from details WHERE useridno=%s",(replyto,))
        # email=cur.fetchone()
        cur.execute("SELECT statement from ciq_details WHERE sno=%s",(ideano,))
        idea=list(cur.fetchone())
        idea=idea[0].split("#$&$#")
        # print(idea)
        idea[2]=answer
        tobeupdated='#$&$#'.join(idea)
        # print(tobeupdated)
        n=cur.execute("SELECT notify from ciq_details WHERE sno=%s",(ideano,))
        up=cur.execute("UPDATE ciq_details SET status=%s WHERE sno=%s ", (0,ideano,))
        # print(" kkkkk: ",session['user_id'],answer)
        #tobeupdated=str([idea[0],name,answer])
        # print(idea,name)
        cur.execute("SELECT ciq_flag from ciq_details WHERE sno=%s",(ideano,))
        flag=cur.fetchone()[0]
        # print(flag)
        # tobeupdated=idea[0]+"#$&$#"+name[0]+"#$&$#"+answer

        up=cur.execute("UPDATE ciq_details SET statement=%s WHERE sno=%s ", (tobeupdated,ideano,))
        # if n:
        #     message="You have been received your response \n For the query: "+ idea[0] +"\n \n" + answer
        #     sendgridmail(email,message)
        mysql.connection.commit()
        # print(up)
        flash("Reply has been edited Successfully")
        if(flag=='i'):
            #return render_template("faculty_idea.html")
            return redirect(url_for('faculty_idea'))
        elif(flag=='q'):
            return redirect(url_for('faculty_question'))
            # return render_template("faculty_question.html")
        else:
            return redirect(url_for('faculty_complaint'))
            # return render_template("faculty_complaint.html")


#retrieving latest rows from ideas table {[...This should also be implemented for questions and complaints as well...]}
@app.route("/latesti") 
@login_required  
def latesti():
    session['viewed'] = False
    session['latest'] = True
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM ciq_details WHERE status=%s AND ciq_flag=%s", (1,'i',))
    mysql.connection.commit()
    rows=cur.fetchall()
    return render_template("faculty_idea.html", records = rows)



#retrieving latest rows from qns table {[...This should also be implemented for questions and complaints as well...]}
@app.route("/latestq") 
@login_required  
def latestq():
    session['viewed'] = False
    session['latest'] = True
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM ciq_details WHERE status=%s AND ciq_flag=%s", (1,'q',))
    mysql.connection.commit()
    rows=cur.fetchall()
    return render_template("faculty_question.html", records = rows)


#retrieving latest rows from ideas table {[...This should also be implemented for questions and complaints as well...]}
@app.route("/latestc") 
@login_required  
def latestc():
    session['viewed'] = False
    session['latest'] = True
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM ciq_details WHERE status=%s AND ciq_flag=%s", (1,'c',))
    mysql.connection.commit()
    rows=cur.fetchall()
    return render_template("faculty_complaint.html", records = rows)


#retrieving viewed rows from ideas table {[...This should also be implemented for questions and complaints as well...]}
@app.route("/viewedi") 
@login_required   
def viewedi():
    session['latest'] = False
    session['viewed'] = True
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM ciq_details WHERE status=%s AND ciq_flag=%s", (0,'i',))
    mysql.connection.commit()
    rows=cur.fetchall()   
    rows1=[]
    rows=list(rows)
    for row in rows:
        row=list(row)
        row[5]=row[5].split("#$&$#")
        rows1.append(row)
    print(rows1)
    return render_template("faculty_idea.html", records = rows1)



#retrieving viewed rows from qns table {[...This should also be implemented for questions and complaints as well...]}
@app.route("/viewedq") 
@login_required   
def viewedq():
    session['latest'] = False
    session['viewed'] = True
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM ciq_details WHERE status=%s AND ciq_flag=%s", (0,'q',))
    mysql.connection.commit()
    rows=cur.fetchall()   
    rows1=[]
    rows=list(rows)
    for row in rows:
        row=list(row)
        row[5]=row[5].split("#$&$#")
        rows1.append(row)
    print(rows1)
    return render_template("faculty_question.html", records = rows1)



#retrieving viewed rows from complaints table {[...This should also be implemented for questions and complaints as well...]}
@app.route("/viewedc") 
@login_required   
def viewedc():
    session['latest'] = False
    session['viewed'] = True
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM ciq_details WHERE status=%s AND ciq_flag=%s", (0,'c',))
    mysql.connection.commit()
    rows=cur.fetchall()   
    rows1=[]
    rows=list(rows)
    for row in rows:
        row=list(row)
        row[5]=row[5].split("#$&$#")
        rows1.append(row)
    print(rows1)
    return render_template("faculty_complaint.html", records = rows1)

#retrieving studentview rows from ideas, questions and complaints tables 
@app.route("/studentview") 
@login_required   
def studentview():
    cur = mysql.connection.cursor()
    print(session['user_id'])
    cur.execute("SELECT statement FROM ciq_details WHERE studentid = %s AND status= %s", (session['user_id'],0,))
    statements=cur.fetchall()
    mylist=[]
    for statement in statements:
        for i in statement:
            print(mylist.append(i.split("#$&$#")))
    print(mylist)
    print(type(mylist))
    # cur.execute("SELECT statement FROM ciq_details WHERE studentid = %s AND status= %s", (session['user_id'],1,))
    # statements.extend(cur.fetchall())
    # cur.execute("SELECT statement FROM ciq_details WHERE studentid = %s AND status= %s", (session['user_id'],1,))
    # statements.extend(cur.fetchall())
    mysql.connection.commit()   
    return render_template("studentview.html", records=mylist)


#retrieving responded rows from ideas, questions and complaints tables 
@app.route("/responded") 
@login_required   
def responded():
    cur = mysql.connection.cursor()
    print(session['user_id'])
    cur.execute("SELECT statement FROM ciq_details WHERE studentid = %s AND status= %s", (session['user_id'],0,))
    statements=cur.fetchall()
    mylist=[]
    for statement in statements:
        for i in statement:
            print(mylist.append(i.split("#$&$#")))
    print(mylist)
    print(type(mylist))
    mysql.connection.commit()   
    return render_template("studentview.html", records=mylist)



#retrieving responded rows from ideas, questions and complaints tables 
@app.route("/yettorespond") 
@login_required   
def yettorespond():
    cur = mysql.connection.cursor()
    print(session['user_id'])
    cur.execute("SELECT statement FROM ciq_details WHERE studentid = %s AND status= %s", (session['user_id'],1,))
    statements=cur.fetchall()
    mylist=[]
    for statement in statements:
        for i in statement:
            print(mylist.append(i.split("#$&$#")))
    print(mylist)
    print(type(mylist))
    mysql.connection.commit()   
    return render_template("studentview.html", records=mylist)


#logging out :)
@app.route("/logout") 
@login_required   
def logout():
    session.clear()
    return redirect("/")


if __name__ == '__main__':
    app.run(host='0.0.0.0',debug = True,port = 8080)
