#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib


SALT = "cs3083"
app = Flask(__name__)
conn = pymysql.connect(host='localhost',
                       port = 3306,
                       user='root',
                       password='',
                       db='Finstagram',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor,
                       autocommit= True)

#Define a route to hello function
@app.route('/')
def hello():
    return render_template('index.html')

#Define route for login
@app.route('/login')
def login():
    return render_template('login.html')

#Define route for register
@app.route('/register')
def register():
    return render_template('register.html')

#Authenticates the login
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    if request.form:
        username = request.form['username']
        password = request.form['password'] + SALT
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

    cursor = conn.cursor()
    query = 'SELECT * FROM Person WHERE username = %s and password = %s'
    cursor.execute(query, (username, password_hash))
    data = cursor.fetchone()
    cursor.close()

    if(data):
        session['username'] = username
        return redirect(url_for('home'))
    else:
        error = 'Invalid login or username. Please try again.'
        return render_template('login.html', error=error)
    error = "An unknown error has occurred. Please try again."
    return render_template("login.html", error = error)

#Authenticates the register
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    if request.form:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        username = request.form['username']
        password = request.form['password'] + SALT
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        email = request.form['email']

    cursor = conn.cursor()
    query = 'SELECT * FROM Person WHERE username = %s'
    cursor.execute(query, (username))
    data = cursor.fetchone()
    if(data):
        error = "This username already exists. Please try again."
        return render_template('register.html', error = error)
    else:
        query = 'INSERT INTO Person (username, password, firstName, lastName, email) VALUES (%s, %s, %s, %s, %s)'
        cursor.execute(query, (username, password_hash, first_name, last_name, email))
        conn.commit()
        cursor.close()
        return render_template('index.html')

    error = "An unknown error has occurred. Please try again."
    return render_template("register.html", error = error)

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

@app.route('/home')
def home():
    username = session['username']
    cursor = conn.cursor()
    query = 'SELECT firstName, lastName FROM Person WHERE username = %s'
    cursor.execute(query, (username))
    names = cursor.fetchone()
    cursor.close()

    return render_template('home.html', username = username, names = names)

#Feature 1 and 2
@app.route("/photos")
def view_photos():
    username = session['username']
    cursor = conn.cursor()
    #Query to get all images the user has access to
    #imaages that they POST
    #images that the people they are following POST
    #images that have been shared with them in a friend group
    #join all three then pass into the html
    query = 'SELECT DISTINCT photo.pID, photo.filePath, person.firstName, \
    person.lastName, photo.postingDate, tag.username as Tagged_user, \
    tagged_person.firstName as Tagged_fName, tagged_person.lastName as Tagged_lName, \
    reactto.username as Reacted_user, reactto.emoji FROM (\
    (SELECT pID FROM photo WHERE poster = %s) UNION ALL \
    (SELECT pID FROM photo INNER JOIN follow ON follow.followee = photo.poster\
     WHERE followStatus = 1 AND allFollowers = 1 AND follower = %s)\
    UNION ALL (SELECT pID FROM sharedwith\
    NATURAL JOIN belongto WHERE username = %s)) a\
    NATURAL JOIN photo\
    LEFT OUTER JOIN person on photo.poster = person.username\
    LEFT OUTER JOIN tag on photo.pID = tag.pID\
    LEFT OUTER JOIN person as tagged_person on tag.username = tagged_person.username\
    LEFT OUTER JOIN reactto on photo.pID = reactto.pID\
    ORDER BY postingDate DESC'

    cursor.execute(query, (username, username, username))
    pID = cursor.fetchall()
    cursor.close()
    if (pID):
        return render_template("photos.html", pID = pID)
    else:
        error = "No photos to show."
        return render_template("photos.html", error = error)

#Feature 3
#@app.route("/post")
#def post_photo():
    #return render_template('post.html')
#Feature 4

#Feature 5

app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
