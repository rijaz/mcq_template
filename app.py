from flask import Flask, render_template, request, url_for, redirect
from flask import session
import sqlite3
import config

app = Flask(__name__)
app.secret_key = config.flask_key

q_dict = {}

@app.route("/")
def main():
    return render_template('signup.html')

@app.route("/signup", methods=['POST','GET'])
def signup():
    if request.method =="POST":
        try:
            #Get the submitted values
            nm = request.form['name']
            eml = request.form['email']
            pref = request.form['service_type']

            #Connect to the database
            con = sqlite3.connect('screen.db')
            cur = con.cursor()
            cur.execute('PRAGMA foreign_keys=ON')

            #Check if the user has already taken the quiz for the service position
            sql = ''' SELECT * FROM Users WHERE name = ? and email = ? and service = ?'''
            cur.execute(sql, (nm,eml, pref))
            rows = cur.fetchall()

            #If they have diplay error message
            if (rows != []):
                error = "You've already made a submission!"
                return render_template("signup.html", error = error)

            values = (nm,eml, pref)

            #If they have not previously submitted, add them to the database
            sql = ''' INSERT INTO Users(name, email, service)
                              VALUES(?, ?, ?) '''
            cur.execute(sql, values)
            user_id = cur.lastrowid
            con.commit()
            con.close()
            error = "Record successfully added "
            #Save the name and service
            session['user_id'] = user_id
            session['user_name'] = nm
            session['user_service'] = pref
            return redirect(url_for("quiz"))

        except:
            error = "There was an error signing up"
            return(render_template("signup.html", error=error))

@app.route("/quiz")
def quiz():
    name = session.get('user_name')
    service_pref = session.get('user_service')

    con = sqlite3.connect('screen.db')
    cur = con.cursor()
    cur.execute('PRAGMA foreign_keys=ON')

    #Get the questions for selected service
    sql = ''' SELECT * FROM Questions WHERE service = ?'''
    cur.execute(sql, (service_pref,))
    rows = cur.fetchall()
    for question in rows:
        q_id = question[0]
        sql = ''' SELECT c_text FROM Choices WHERE q_id = ?'''
        cur.execute(sql, (q_id,))
        answers = cur.fetchall()
        # The SQL returns answers as a list of tuples, extract the relevant value
        q_dict[question[1]] = [i[0] for i in answers]
    session['quiz_info'] = q_dict
    con.close()

    return render_template('quiz.html', service=service_pref, q=q_dict.keys(), o=q_dict)

@app.route('/quiz', methods=['POST'])
def quiz_submit():
    submission = {}
    try:
        #Connect to the database
        con = sqlite3.connect('screen.db')
        cur = con.cursor()
        cur.execute('PRAGMA foreign_keys=ON')

        #Get the question and it's mult-choice answers from session
        quiz_info = session.get('quiz_info')
        session.pop('quiz_info', None)
        user_id = session.get('user_id')
        user_service = session.get('user_service')
        error += user_service

        #Get the submitted answers using request.form where i is the question
        for i in quiz_info:
            submission[i] = request.form[i]
        sorted_keys = sorted(submission.keys())

        #SQL query for eventually updated the user response table with current user
        sql = ''' INSERT INTO User_Submissions(user_id, question_id, choice_id)
                          VALUES(?, ?, ?) '''

        for i in sorted_keys:
            #Get the question's (i's) id, making sure that it is the right service
            q_sql = ''' SELECT id FROM Questions WHERE service = ? AND q_text = ?'''
            cur.execute(q_sql, (user_service, i))
            q_id = cur.fetchone()[0]

            #Get the id of the answer the user selected for the question
            ans_sql = ''' SELECT id FROM Choices WHERE q_id = ? AND c_text = ?'''
            cur.execute(ans_sql, (q_id, submission[i]))
            ans_id = cur.fetchone()[0]

            #Create tuple of user_id, question id and answer id for the submission query and execute
            values = (user_id, q_id, ans_id)
            cur.execute(sql, values)

            #Commit your changes
            con.commit()
        con.close()

    except:
        error = "There was an error submitting your response."

    finally:
        return render_template('index.html', error = error)

@app.route("/admin")
def admin():
    return render_template('admin.html')

@app.route("/admin", methods=['POST'])
def admin_query():
    error=None
    rows=None
    try:
        #Get the query
        query = request.form['query']

        #Connect to the database
        con = sqlite3.connect('screen.db')
        cur = con.cursor()
        cur.execute('PRAGMA foreign_keys=ON')

        cur.execute(query)
        rows = cur.fetchall()
        con.commit()
        con.close()
        return render_template('admin.html', error=error,rows=rows)
    except:
        error = "There was an error executing the query"
        return render_template('admin.html', error=error, rows=rows)

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8000, debug=True)
