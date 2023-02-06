#app.py
from flask import Flask, request, session, redirect, url_for, render_template, flash
import psycopg2 #pip install psycopg2 
import psycopg2.extras
import re 
from werkzeug.security import generate_password_hash, check_password_hash

 
app = Flask(__name__)

app.secret_key = 'project-key'
DB_HOST = "localhost"
DB_NAME = "project"
DB_USER = "postgres"
DB_PASS = "admin"
 
conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST)
 
@app.route('/')
def home():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
   
    # Check if user is loggedin
    if 'loggedin' in session:
        print(session)
        cursor.execute('SELECT * FROM users WHERE role = 1')
        accounts = cursor.fetchall()
        # Show the profile page with account info
        return render_template('home.html', accounts=accounts)
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
   # Redirect to login page
   return redirect(url_for('login'))
  
# @app.route('/profile')
# def profile(): 
#     cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
   
#     # Check if user is loggedin
#     if 'loggedin' in session:
#         cursor.execute('SELECT * FROM users WHERE id = %s', [session['id']])
#         account = cursor.fetchone()
#         cursor.execute('SELECT * FROM users WHERE role = 1')
#         accounts = cursor.fetchall()

#         # Show the profile page with account info
#         return render_template('profile.html', account=account, accounts = accounts)
#     # User is not loggedin redirect to login page
#     return redirect(url_for('login'))

@app.route('/profile/<username>')
def profile_by_id(username): 
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Check if user is loggedin
    if 'loggedin' in session:
        cursor.execute('SELECT * FROM users WHERE username = %s', [username])
        account = cursor.fetchone()
        cursor.execute('SELECT * FROM users')
        users = cursor.fetchall()
        cursor.execute('SELECT * FROM profile_comments WHERE target_id = %s', [account['id']])
        comments = cursor.fetchall()
        if request.method == 'POST' and 'comment' in request.form:
            comment = request.form['comment']
            cursor.execute("INSERT INTO profile_comments (comment, commentator_id, target_id) VALUES (%s,%s,%s)", (comment, session['id'], account['id']))
            conn.commit()

        # Show the profile page with account info
        return render_template('profile.html', account=account,comments=comments,users=users)
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



@app.route('/add-game',methods=['GET', 'POST'])
def addgame(): 
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST' and 'title' in request.form and 'description' in request.form and 'genre' in request.form and 'release_date' in request.form:
        # Create variables for easy access
        title = request.form['title']
        description = request.form['description']
        genre = request.form['genre']
        release_date = request.form['release_date']

 
        #Check if game exists 
        cursor.execute('SELECT * FROM games WHERE title = %s', (title,))
        game = cursor.fetchone()
        print(game)
        # If account exists show error and validation checks
        if game:
            flash('Game already exists!')
        else:
            # Game doesnt exists and the form data is valid, now insert new game into games table
            cursor.execute("INSERT INTO games (title, description, genre,release_date) VALUES (%s,%s,%s,%s)", (title, description, genre,release_date))
            conn.commit()
            return redirect(url_for('games'))

    elif request.method == 'POST':
        # Form is empty... (no POST data)
        flash('Please fill out the form!')
    # Show registration form with message (if any)   
    return render_template('add-game.html')


@app.route('/games/<title>')
def profile_by_title(title): 
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    # Check if user is loggedin
    if 'loggedin' in session:
        cursor.execute('SELECT * FROM games WHERE title = %s', [title])
        game = cursor.fetchone()
        cursor.execute('SELECT * FROM game_comments WHERE game_id = %s', [game[0]])
        comments = cursor.fetchall()
        print(comments)
        cursor.execute('SELECT * FROM users')
        users = cursor.fetchall()
        return render_template('game.html', game=game,comments=comments,users=users)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

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
        cursor.execute('SELECT * FROM guides WHERE id = %s', (guide_id,))
        guide = cursor.fetchone()
        # print(guides)
        # cursor.execute('SELECT * FROM users')
        # users = cursor.fetchall()
        return render_template('guide.html', guide = guide)
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))


@app.route('/games/<title>',methods=['GET', 'POST'])
def addcomment(title): 
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if request.method == 'POST' and 'comment' in request.form:
        # Create variables for easy access
        comment = request.form['comment']
        #Check if game exists 
        cursor.execute('SELECT * FROM games WHERE title = %s', (title,))
        game = cursor.fetchone()
        print(game)
        cursor.execute("INSERT INTO game_comments (comment, game_id, user_id) VALUES (%s,%s,%s)", (comment, game[0], session['id']))
        conn.commit()
        cursor.execute('SELECT * FROM game_comments WHERE game_id = %s', [game[0]])
        print(game)
        comments = cursor.fetchall()
        # # If account exists show error and validation checks
        # if game:
        #     flash('Game already exists!')
        # else:
        #     # Game doesnt exists and the form data is valid, now insert new game into games table
        #     cursor.execute("INSERT INTO games (title, description, genre,release_date) VALUES (%s,%s,%s,%s)", (title, description, genre,release_date))
        #     conn.commit()
        #     return redirect(url_for('games'))
        return render_template('game.html',game=game,comments=comments)




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
    

if __name__ == "__main__":
    app.run(debug=True)