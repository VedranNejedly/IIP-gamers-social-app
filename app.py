#app.py
from flask import Flask, request, session, redirect, url_for, render_template, flash
import psycopg2 #pip install psycopg2 
import psycopg2.extras
import re 
import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename



UPLOAD_FOLDER='static\images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


app.secret_key = 'project-key'
# DB_HOST = "localhost"
# DB_NAME = "project"
# DB_USER = "postgres"
# DB_PASS = "admin"

DB_HOST = "manny.db.elephantsql.com"
DB_NAME = "nihgowhd"
DB_USER = "nihgowhd"
DB_PASS = "QO1Pid80tjfV2OXC9BdRZb_2BDLnyjEE"

# roxvyxky
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS


conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
@app.route('/')
def home():
    # cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
   
    # Check if user is loggedin
    if 'loggedin' in session:
        print(session)
        # cursor.execute('SELECT * FROM users WHERE role = 1')
        # accounts = cursor.fetchall()
        # Show the profile page with account info
        return render_template('home.html')
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

    # # Check if user is loggedin
    # if 'loggedin' in session:
    
    #     # User is loggedin show them the home page
    #     return render_template('home.html', username=session['username'])
    # # User is not loggedin redirect to login page
    # return redirect(url_for('login'))



@app.route('/login/', methods=['GET', 'POST'])
def login():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
   
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        print(password)
 
        # Check if account exists using MySQL
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        # Fetch one record and return result
        account = cursor.fetchone()
 
        if account:
            password_rs = account['password']
            print(password_rs)
            # If account exists in users table in out database
            if check_password_hash(password_rs, password):
                # Create session data, we can access this data in other routes
                session['loggedin'] = True
                session['id'] = account['id']
                session['username'] = account['username']
                session['role'] = account['role']
                    # Redirect to home page
                return redirect(url_for('home'))
            else:
                # Account doesnt exist or username/password incorrect
                flash('Incorrect username/password', category='error')
        else:
            # Account doesnt exist or username/password incorrect
            flash('Incorrect username/password', category='error')
 
    return render_template('login.html')
  
@app.route('/register', methods=['GET', 'POST'])
def register():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
 
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
    
        _hashed_password = generate_password_hash(password)
 
        #Check if account exists using MySQL
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()
        print(account)
        # If account exists show error and validation checks
        if account:
            flash('Account already exists!')
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            flash('Invalid email address!')
        elif not re.match(r'[A-Za-z0-9]+', username):
            flash('Username must contain only characters and numbers!')
        elif not username or not password or not email:
            flash('Please fill out the form!')
        else:
            # Account doesnt exists and the form data is valid, now insert new account into users table
            cursor.execute("INSERT INTO users (username, password, email) VALUES (%s,%s,%s)", (username, _hashed_password, email))
            conn.commit()
            flash('You have successfully registered!')
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        flash('Please fill out the form!')
    # Show registration form with message (if any)
    return render_template('register.html')
   
   
@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   session.pop('role',None)
   # Redirect to login page
   return redirect(url_for('login'))
  
@app.route('/profiles-admin')
def profilesAdmin(): 
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if not 'loggedin' in session:
        return redirect(url_for('login'))
    # Check if user is loggedin
    if session['role'] == 2:
        cursor.execute('SELECT * FROM users WHERE role = 1')
        accounts = cursor.fetchall()
        # Show the profile page with account info
        return render_template('profiles-admin.html', accounts = accounts)
    # User is not loggedin redirect to login page
    return redirect(url_for('home'))

@app.route('/profiles-admin/<id>')
def deleteAccount(id):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('DELETE FROM users WHERE id = %s',(id))
    conn.commit()
    cursor.execute('SELECT * FROM users WHERE role = 1')
    accounts = cursor.fetchall()
    return render_template('profiles-admin.html', accounts = accounts)



@app.route('/profile/<username>')
def profile_by_id(username): 
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Check if user is loggedin
    if 'loggedin' in session:
        cursor.execute('SELECT * FROM users WHERE username = %s', [username])
        account = cursor.fetchone()
        cursor.execute('SELECT * FROM games')
        games = cursor.fetchall()
        cursor.execute('SELECT * FROM users')
        users = cursor.fetchall()
        cursor.execute('SELECT * FROM user_plays WHERE user_id =%s',(account[0],))
        user_plays = cursor.fetchall()
        cursor.execute('SELECT * FROM profile_comments WHERE target_id = %s', [account['id']])
        comments = cursor.fetchall()
        if request.method == 'POST' and 'comment' in request.form:
            comment = request.form['comment']
            cursor.execute("INSERT INTO profile_comments (comment, commentator_id, target_id) VALUES (%s,%s,%s)", (comment, session['id'], account['id']))
            conn.commit()

        # Show the profile page with account info
        return render_template('profile.html', account=account,comments=comments,users=users,user_plays=user_plays,games=games)
    # User is not loggedin redirect to login page


@app.route('/profile/<username>',methods=['GET', 'POST'])
def profileComment(username): 
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
    account = cursor.fetchone()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    cursor.execute('SELECT * FROM profile_comments WHERE target_id = %s', [account['id']])
    comments = cursor.fetchall()
    if request.method == 'POST' and 'comment' in request.form:
        # Create variables for easy access
        comment = request.form['comment']
        # Check if game exists 
        cursor.execute("INSERT INTO profile_comments (comment, commentator_id, target_id) VALUES (%s,%s,%s)", (comment, session['id'], account['id']))
        conn.commit()
        cursor.execute('SELECT * FROM profile_comments where target_id = %s', [account['id']])
        comments = cursor.fetchall()
        return render_template('profile.html',account=account,comments=comments,users=users)
    
@app.route('/profile/<username>/<comment_id>',methods=['GET', 'POST'])
def deleteProfileComment(comment_id,username):
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('DELETE FROM profile_comments WHERE id = %s',(comment_id,))
    cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
    account = cursor.fetchone()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    cursor.execute('SELECT * FROM profile_comments WHERE target_id = %s', [account['id']])
    comments = cursor.fetchall()
    conn.commit()
    return render_template('profile.html', account=account,comments=comments,users=users )




@app.route('/games/<title>',methods=['GET', 'POST'])
def addcomment(title): 
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT * FROM games WHERE title = %s', (title,))
    game = cursor.fetchone()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    cursor.execute('SELECT * FROM game_comments WHERE game_id = %s', [game[0]])
    comments = cursor.fetchall()
    if request.method == 'POST' and 'comment' in request.form:
        # Create variables for easy access
        comment = request.form['comment']
        # Check if game exists 
        cursor.execute("INSERT INTO game_comments (comment, user_id, game_id) VALUES (%s,%s,%s)", (comment, session['id'], game[0]))
        conn.commit()
        cursor.execute('SELECT * FROM game_comments where game_id = %s', [game[0]])
        comments = cursor.fetchall()
    return render_template('game.html',game=game,comments=comments,users=users)



@app.route('/games')
def games(): 
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
   
    # Check if user is loggedin
    if 'loggedin' in session:
        cursor.execute('SELECT * FROM games')
        games = cursor.fetchall()
        # Show the profile page with account info
        return render_template('games.html', games=games)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


# @app.route('/',methods=['POST'])
# def upload_image():
#   if request.method == 'POST':
#         # check if the post request has the file part
#         if 'file' not in request.files:
#             flash('No file part')
#             return redirect(request.url)
#         file = request.files['file']
#         # If the user does not select a file, the browser submits an
#         # empty file without a filename.
#         if file.filename == '':
#             flash('No selected file')
#             return redirect(request.url)
#         if file and allowed_file(file.filename):
#             filename = secure_filename(file.filename)
#             file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#             return redirect(request.url)

@app.route('/add-game',methods=['GET', 'POST'])
def addgame(): 
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST' and 'title' in request.form and 'file' in request.files and 'description' in request.form and 'genre' in request.form and 'release_date' in request.form:

        title = request.form['title']
        description = request.form['description']
        genre = request.form['genre']
        release_date = request.form['release_date']
        file = request.files['file']
 
        #Check if game exists 
        cursor.execute('SELECT * FROM games WHERE title = %s', (title,))
        game = cursor.fetchone()
        print(game)
        # If account exists show error and validation checks
        if game:
            flash('Game already exists!')
        else:
            # Game doesnt exists and the form data is valid, now insert new game into games table

            if file and allowed_file(file.filename):
                splitName = file.filename.rsplit(".")
                filename = secure_filename(title)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename+'.'+splitName[1]))
            cursor.execute("INSERT INTO games (title, description, genre,release_date) VALUES (%s,%s,%s,%s)", (title, description, genre,release_date))
            conn.commit()
            return redirect(url_for('games'))
        

    elif request.method == 'POST':
        # Form is empty... (no POST data)
        flash('Please fill out the form!')
    # Show registration form with message (if any)   
    return render_template('add-game.html')


@app.route('/games/<title>',methods=['GET', 'POST'])
def profile_by_title(title): 
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Check if user is loggedin
    

    if 'loggedin' in session:
        cursor.execute('SELECT * FROM games WHERE title = %s', [title])
        game = cursor.fetchone()
        cursor.execute('SELECT * FROM game_comments WHERE game_id = %s', [game[0]])
        comments = cursor.fetchall()
        cursor.execute('SELECT * FROM ranks WHERE game_id = %s', [game[0]])
        ranks = cursor.fetchall()
        cursor.execute('SELECT * FROM users')
        users = cursor.fetchall()
        #     # Create variables for easy access
        #     rank = request.form['rank']
        #     cursor.execute('SELECT * FROM user_plays WHERE user_id   = %s', [session['id']])
        #     flag = cursor.fetchall()
        #     print("flag flag flag")
        #     print(flag)
        #     cursor.execute("INSERT INTO user_plays (user_id,game_id, rank) VALUES (%s,%s,%s)", (session['id'], game[0], rank))
        #     conn.commit()
        #     return redirect(url_for('games'))

            
        return render_template('game.html', game=game,comments=comments,users=users,ranks=ranks)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


@app.route('/games/<title>/set-rank',methods=['GET', 'POST'])
def setRank(title): 
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT * FROM games WHERE title = %s', [title])
    game = cursor.fetchone()
    cursor.execute('SELECT * FROM ranks WHERE game_id = %s', [game[0]])
    ranks = cursor.fetchall()
    if request.method == 'POST' and 'rank' in request.form:
        cursor.execute("SELECT * FROM user_plays WHERE user_id =%s",[session['id']])
        flag = cursor.fetchone()
        rank = request.form['rank']
        if flag:
            cursor.execute("UPDATE user_plays SET rank = %s WHERE user_id=%s",[rank,session['id']])
            conn.commit()
            return redirect(url_for('profile_by_title',title = title))
        else:
            cursor.execute("INSERT INTO user_plays (user_id,game_id, rank) VALUES (%s,%s,%s)", (session['id'], game[0], rank))
            conn.commit()
            return redirect(url_for('profile_by_title',title = title))
    return render_template('set-rank.html',game=game,ranks = ranks)


@app.route('/games/<title>/guides')
def getGuides(title): 
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Check if user is loggedin
    if 'loggedin' in session:
        cursor.execute('SELECT * FROM games WHERE title = %s', (title,))
        game = cursor.fetchone()
        cursor.execute('SELECT * FROM guides WHERE game_id = %s', [game[0]])
        guides = cursor.fetchall()
        # print(guides)
        # cursor.execute('SELECT * FROM users')
        # users = cursor.fetchall()
        return render_template('guides.html', guides=guides, game= game)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/games/<title>/guides/<guide_id>')
def getGuide(title,guide_id): 
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Check if user is loggedin
    if 'loggedin' in session:
        # cursor.execute('SELECT * FROM games WHERE title = %s', (title,))
        # game = cursor.fetchone()
        cursor.execute('SELECT * FROM games WHERE title = %s', (title,))
        game = cursor.fetchone()
        print(guide_id)
        cursor.execute('SELECT * FROM guides WHERE id = %s', (guide_id,))
        guide = cursor.fetchone()
        # print(guides)
        # cursor.execute('SELECT * FROM users')
        # users = cursor.fetchall()
        return render_template('guide.html', guide = guide, game = game)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


@app.route('/games/<title>/guides/<guide_id>/delete')
def deleteGuide(title,guide_id): 
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Check if user is loggedin
    if 'loggedin' in session:
        cursor.execute('SELECT * FROM games WHERE title = %s', (title,))
        game = cursor.fetchone()
        cursor.execute('DELETE FROM guides WHERE id = %s', (guide_id,))
        cursor.execute('SELECT * FROM guides WHERE game_id = %s', [game[0]])
        guides = cursor.fetchall()
        conn.commit()

        return redirect(url_for('getGuides',title = title))

        # return render_template('guides.html', guides=guides, game = game)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/games/<title>/guides/add-guide',methods=['GET', 'POST'])
def addGuide(title): 
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST' and 'title' in request.form and 'guide_text' in request.form:
        # Create variables for easy access
        guide_title = request.form['title']
        guide_text = request.form['guide_text']
        youtube_link = request.form['youtube_link']
        #Check if game exists 
        cursor.execute('SELECT * FROM games WHERE title = %s', (title,))
        game = cursor.fetchone()
        # Game doesnt exists and the form data is valid, now insert new game into games table
        if youtube_link:
            cursor.execute("INSERT INTO guides (title, guide_text, youtube_link,game_id,user_id) VALUES (%s,%s,%s,%s,%s)", (guide_title, guide_text, youtube_link,game[0],session['id']))
            conn.commit()
        else:
            cursor.execute("INSERT INTO guides (title, guide_text,game_id,user_id) VALUES (%s,%s,%s,%s)", (guide_title, guide_text,game[0],session['id']))
            conn.commit()
        # return render_template('add-guide.html')
        return redirect(url_for('getGuides',title = title))
    
    return render_template('add-guide.html',title=title)


@app.route('/games/<title>/playerbase',methods=['GET', 'POST'])
def fetchPlayerbase(title): 
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT * FROM games WHERE title =%s',(title,))
    game=cursor.fetchone()
    cursor.execute('SELECT * FROM user_plays WHERE game_id =%s',[game[0]])
    playerbase=cursor.fetchall()
    cursor.execute('SELECT * FROM users ')
    users=cursor.fetchall()
    cursor.execute('SELECT * FROM ranks WHERE game_id =%s ',[game[0]])
    ranks=cursor.fetchall()
    if request.method == 'POST' and 'rank' in request.form:
        rank = request.form['rank']
        print(rank)
        if rank != 'all':
            cursor.execute('SELECT * FROM user_plays WHERE game_id =%s AND rank=%s',[game[0],rank])
            playerbase=cursor.fetchall()
    return render_template('game-playerbase.html',title=title,playerbase=playerbase,users=users,ranks=ranks,game=game)



@app.route('/remove-game',methods=['GET', 'POST'])
def removegame(): 
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT * FROM games')
    listofgames = cursor.fetchall()
    if request.method == 'POST' and 'title' in request.form:
        title = request.form['title']
        cursor.execute('SELECT * FROM games WHERE title = %s', (title,))
        game = cursor.fetchone()
        cursor.execute('DELETE FROM games WHERE title = %s',(title,))
        conn.commit()
        return redirect(url_for('games'))
    return render_template('remove_game.html',listofgames=listofgames)
    

@app.route('/add-ranks',methods=['GET', 'POST'])
def addRanks(): 
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute('SELECT * FROM games')
    listofgames = cursor.fetchall()
    if request.method == 'POST' and 'title' in request.form and 'rank' in request.form:
        title = request.form['title']
        rank = request.form['rank']
        cursor.execute('SELECT * FROM games WHERE title = %s', (title,))
        game = cursor.fetchone()
        if rank and title:
            cursor.execute("INSERT INTO ranks (rank_name, game_id) VALUES (%s,%s)", (rank, game[0]))
            conn.commit()
        return redirect(url_for('games'))
    return render_template('add-ranks.html',listofgames=listofgames)
    


if __name__ == "__main__":
    app.run()
    # app.run(debug=False,host='0.0.0.0')