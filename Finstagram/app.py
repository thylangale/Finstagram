#Import Flask Library
from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors
import hashlib
import datetime


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
@app.route('/post')
def post():
    return render_template('post.html')

@app.route("/postPhoto", methods=['GET', 'POST'])
def post_photo():
    cursor = conn.cursor()
    if request.form:
        filePath = request.form['location']
        allFollowers = request.form['allFollowers']
        caption = request.form['caption']
        if (allFollowers == 'yes'):
            allFollowers = True
        else:
            allFollowers = False
        username = session['username']
        time = datetime.datetime.now()
        query = 'INSERT INTO Photo (postingDate, filePath, allFollowers, caption, poster) \
        VALUES (%s, %s, %s, %s, %s)'
        cursor.execute(query, (time, filePath, allFollowers, caption, username))
        conn.commit()
        cursor.close()
        success = "Photo Posted!"
        return render_template('post.html', success = success)

    error = "Unable to post photo"
    return render_template('post.html', error = error)


#Feature 4
@app.route('/follow')
def follow():
    return render_template('follow.html')
@app.route("/followUser", methods=['GET', 'Post'])
def manage_follows():
    cursor = conn.cursor()
    if request.form:
        follow = request.form['follow']
        username = session['username']

        query = 'SELECT * FROM Follow WHERE follower = %s AND followee = %s'
        cursor.execute(query, (username, follow))
        data = cursor.fetchone()
        if(data):
            error = "Follow Request Already Sent."
            return render_template('follow.html', error = error)
        else:
            notFollowing = 0
            query = 'INSERT INTO Follow (follower, followee, followStatus) VALUES (%s, %s,%s)'
            cursor.execute(query, (username, follow, notFollowing))
            conn.commit()
            cursor.close()
            success = "Follow Request Sent"
            return render_template('follow.html', success = success)
    error = "Unable to follow"
    return render_template('follow.html', error = error)

@app.route("/requests")
def followrequests():
    username = session['username']
    cursor = conn.cursor()
    query = 'SELECT * FROM follow WHERE followee = %s AND followStatus = 0'
    cursor.execute(query, (username))
    allRequests = cursor.fetchall()
    cursor.close()
    if (allRequests):
        return render_template("requests.html", allRequests = allRequests)
    else:
        error = "No follow requests."
        return render_template("requests.html", error = error)

@app.route("/acceptRequest", methods=['GET', 'POST'])
def acceptRequest():
    cursor = conn.cursor()
    if request.form:
        follower = request.form['accept']
        username = session['username']

        query = 'SELECT * FROM Follow WHERE follower = %s AND followee = %s AND followStatus = 0'
        cursor.execute(query, (follower, username))
        data = cursor.fetchone()
        query2 = 'SELECT * FROM follow WHERE followee = %s AND followStatus = 0'
        cursor.execute(query2, (username))
        allRequests = cursor.fetchall()

        if(data):
            query = 'UPDATE Follow SET followStatus = 1 WHERE follower = %s AND followee = %s'
            cursor.execute(query, (follower, username))
            conn.commit()
            cursor.close()
            success = "Follower Accepted!"
            return render_template('requests.html', success = success, allRequests = allRequests)
        else:
            error = "Cannot Accept Request"
            return render_template('requests.html', error = error, allRequests = allRequests)

    error = "Unable to accept follow"
    return render_template('requests.html', error = error)

#Feature 5
@app.route("/friendGroups")
def friendGroups():
    return render_template('friendGroups.html')

@app.route("/addFriendGroup", methods=['GET', 'POST'])
def addFriendGroup():
    cursor = conn.cursor()
    if request.form:
        name = request.form['name']
        description = request.form['description']
        username = session['username']
        query = 'SELECT * FROM Friendgroup WHERE groupName = %s AND groupCreator = %s'
        cursor.execute(query, (name, username))
        data = cursor.fetchone()
        if (data):
            error = "You already have a group with this name"
            return render_template('friendGroups.html', error = error)
        else:
            query = 'INSERT INTO Friendgroup (groupName, groupCreator, description) VALUES (%s, %s, %s)'
            cursor.execute(query, (name, username, description))
            query2 = 'INSERT INTO Belongto (username, groupName, groupCreator) VALUES (%s, %s, %s)'
            cursor.execute(query2, (username, name, username))
            conn.commit()
            cursor.close()
            success = "FriendGroup created!"
            return render_template('friendGroups.html', success = success)

    error = "Unable to add Friend Group"
    return render_template('friendGroups.html', error = error)



app.secret_key = 'some key that you will never guess'
#Run the app on localhost port 5000
#debug = True -> you don't have to restart flask
#for changes to go through, TURN OFF FOR PRODUCTION
if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
