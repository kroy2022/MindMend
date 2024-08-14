#app.py flask file
from base64 import b64decode
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect 
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi
from flask_socketio import SocketIO, emit, join_room
from groq import Groq
from typing import List
from pydantic import BaseModel
from key import hugging_face, groq_key, quizme_email, quizme_password, gmail_server, gmail_port
from langchain_community.tools import YouTubeSearchTool
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import PyPDF2, openai , pyodbc, base64, requests, json, smtplib, threading 

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="http://localhost:5173") #*
CORS(app)
csrf = CSRFProtect(app)
conn_str = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=revix-db.c5s660oustdd.us-east-2.rds.amazonaws.com,1433;"
    "Database=QuizMeDB;"
    "Uid=admin;"
    "Pwd=r3viXaiP&ssw0rd;"
)

client = Groq(
    api_key=groq_key,
)

@socketio.on('join_room')
def handle_join_room(data):
    user_id = data.get('user_id')
    room = data.get('room')
    if user_id and room:
        same_room = ''.join(sorted([user_id, room]))
        join_room(same_room)
    else:
        return jsonify({
            "status": "Error"
        })

@socketio.on('send_message')
def handle_message(data):
    message = data.get("message")
    user_id = data.get("user_id")
    recipient_id = data.get("recipient_id")

    if user_id == None or recipient_id == None:
        return
    
    current_date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        sql = """
        INSERT INTO MESSAGE (Sender_ID, Recipient_ID, Time, Message_Content) 
        OUTPUT INSERTED.Message_ID
        VALUES (?, ?, ?, ?)
        """
        cursor.execute(sql, (user_id, recipient_id, current_date_str, message))
        message_id = cursor.fetchone()[0]
        conn.commit() 
        same_room = ''.join(sorted([user_id, recipient_id]))
        emit('recieve_message', {'message': message, "sender": user_id, "time_sent": current_date_str, "message_id": message_id }, room=same_room)
        cursor.close()
        conn.close()
    except pyodbc.Error as e:
            # Handle exceptions
            conn.rollback()  # Rollback transaction in case of error
            cursor.close()
            conn.close()
            return jsonify({"status": "Error", "message": str(e)})


@app.route('/Login', methods=["POST"])
@csrf.exempt
def get_login_info():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    userType = request.form.get("type")
    username = request.form.get('username').lower()
    password = request.form.get('password')
    longitude = request.form.get("longitude")
    latitude = request.form.get("latitude")

    if userType == "existing":
        try:
            # Verify login
            cursor.execute("SELECT * FROM Users WHERE User_ID = ? AND Password = ?", (username, password))
            user = cursor.fetchone()

            if user:
                age = calculate_age(user[8])

                # Update last login time, location, and age
                current_date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute("UPDATE Users SET Last_login = ?, Longitude = ?, Latitude = ?, Age = ? WHERE User_ID = ?", 
                            (current_date_str, longitude, latitude, age, username))
            
                #Get Custom Sets
                cursor.execute("SELECT * FROM StudySet WHERE User_ID = ?", (username,))
                study_sets = cursor.fetchall()
                sets = []
                for study_set in study_sets:
                    set_information = {
                        "set_id": study_set[1],
                        "public": study_set[3],
                        "title": study_set[4],
                        "description": study_set[5],
                        "summary": study_set[6],
                        "prompt": study_set[7],
                        "created": study_set[8]
                    }
                    sets.append(set_information)
                
                #Fetch Default Sets
                cursor.execute("Select * From StudySet Where DefaultSet = 1")
                defaultSets = cursor.fetchall()
                default_sets = []
                for default_set in defaultSets:
                    tempSet = {
                        "set_id": default_set[1],
                        "title": default_set[4],
                        "summary": default_set[6],
                        "prompt": default_set[7],
                        "description": default_set[5]
                    }          
                    default_sets.append(tempSet)

                #Fetch Public Sets
                cursor.execute("Select * From StudySet Where PublicSet = 1")
                publicSets = cursor.fetchall()
                public_sets = []
                for public_set in publicSets:
                    tempSet = {
                        "user_id": public_set[0],
                        "set_id": public_set[1],
                        "title": public_set[4],
                        "description": public_set[5],
                        "summary": public_set[6],
                        "prompt": public_set[7]                  
                    }
                    public_sets.append(tempSet)

                pic = ""
                if user[7] is not None:
                    pic = user[7]
                else:
                    pic = base64.b64encode(user[6]).decode('utf-8')
                                
                cursor.execute("SELECT End_Date, Plan_Name FROM Subscription WHERE User_ID = ?", (username,))
                details = cursor.fetchone()
                plan = None
                if details[1] is not None:
                    plan = {
                        "ending": details[0] if details and details[0] is not None else "",
                        "name": details[1]
                    }

                conn.commit()  # Commit the transaction
                cursor.close()
                conn.close()
                return jsonify({
                    "status": "Valid",
                    "type": "Existing",
                    "name": user[5],
                    "email": user[0],
                    "pfp": pic,
                    "pro": plan,
                    "custom_sets": sets,
                    "default_sets": default_sets,
                    "public_sets": public_sets
                })
            else:
                return jsonify({"status": "Error", "message": "That username or password does not exist. Do you already have an account?"})
        
        except pyodbc.Error as e:
            # Handle exceptions
            conn.rollback()  # Rollback transaction in case of error
            cursor.close()
            conn.close()
            return jsonify({"status": "Error", "message": str(e)})
    else:
        cursor.execute(f"Select * From Users where User_ID = '{username}'")
        db = cursor.fetchall()
        name = request.form.get("name")
        birthday = request.form.get("birthday")
        age = calculate_age(birthday)

        if db:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({
                "status": "Error",
                "message": "That username or password already exists", 
                "code": 409
            })
        
        current_date = datetime.now()
        current_date_str = current_date.strftime('%Y-%m-%d %H:%M:%S')
    
        if password == "oauthUser":
            pic = request.form.get("pfp")
            cursor.execute("INSERT INTO Users (User_ID, Password, Latitude, Longitude, Last_login, Name, Profile_Picture_OAuth, Birthday, Age) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (username, password, latitude, longitude, current_date_str, name, pic, birthday, age))
        else:
            cursor.execute("INSERT INTO Users (User_ID, Password, Latitude, Longitude, Last_login, Name, Profile_Picture_OAuth, Birthday, Age) VALUES (?, ?, ?, ?, ?, ?, NULL, ?, ?)", (username, password, latitude, longitude, current_date_str, name, birthday, age))           
        
        cursor.execute("INSERT INTO Subscription (User_ID, Plan_Name, Price) VALUES (?, ?, ?)", (username, 'Starter', 0))

        conn.commit() 

        #Fetch Default Sets
        cursor.execute("Select * From StudySet Where DefaultSet = 1")
        defaultSet = cursor.fetchall()
        default_sets = []
        for set in defaultSet:
            tempSet = {
                "set_id": set[1],
                "title": set[4],
                "prompt": set[6],
                "summary": set[7],
                "description": set[5],
                "studied": 0
            }          
            default_sets.append(tempSet)

        #Fetch Public Sets
        cursor.execute("Select * From StudySets Where PublicSet = 1")
        publicSets = cursor.fetchall()
        public_sets = []
        for public_set in publicSets:
            tempSet = {
                "user_id": public_set[0],
                "set_id": public_set[1],
                "title": public_set[2],
                "description": public_set[3],
                "summary": public_set[4],
                "prompt": public_set[5]                 
            }
            public_sets.append(tempSet)
        
        plan = {
            "name": "Starter",
            "ending": None
        }
        cursor.close()
        conn.close()

        return jsonify({
            "status": "Valid",
            "type": "Create",
            "custom_sets": None,
            "default_sets": default_sets,
            "public_sets": public_sets,
            "pro": plan,
            "name": name,
            "email": username,
            "pfp": "https://lh3.googleusercontent.com/a/ACg8ocI0UcHo2l_XN3SxMugWKrjl5SjIzXdyxOeC5eOyZGGDi4KNGA=s96-c",
        })        

def calculate_age(birthdate):
    if isinstance(birthdate, str):
        birth_date = datetime.strptime(birthdate, "%Y-%m-%d")
    else:
        birth_date = birthdate

    today = datetime.today()
    age = today.year - birth_date.year

    # Adjust age if birthdate hasn't occurred yet this year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1

    return age

@app.route('/change/pfp', methods=["POST"])
@csrf.exempt 
def change_pfp():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    try: 
        base64_pfp = request.form.get("pfp")
        new_pfp = b64decode(base64_pfp)

        user_id = request.form.get("user_id")
        cursor.execute("Update Users Set Profile_Picture = ? Where User_ID = ?", (new_pfp, user_id))
        conn.commit()

        return jsonify({
            "status": "Valid",
            "type": "pfp",
            "pfp": base64.b64encode(new_pfp).decode('utf-8')
        })
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({
            "status": "Invalid",
            "error": str(e)
        })

@app.route('/change/name', methods=["POST"])
@csrf.exempt 
def change_name():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    try:
        name = request.form.get("name")
        user_id = request.form.get("user_id")

        cursor.execute("Update Users Set Name = ? Where User_ID = ?", (name, user_id))
        conn.commit()

        return jsonify({
            "status": "Valid",
            "type": "name",
            "name": name
        })
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({
            "status": "Invalid",
            "error": str(e)
        })

@app.route('/dashboard/data', methods=["POST"])
@csrf.exempt 
def load_dashboard_data():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    username = request.form.get("username").lower()
    set_id = request.form.get("set_id")

    #Delete User Set
    if set_id:
        try:
            cursor.execute(f"DELETE From StudySet Where User_ID = '{username}' and Set_ID = {set_id}")
            cursor.execute(f"Delete From Flashcard Where User_ID = '{username}' and Set_ID = {set_id}")
            conn.commit()
        except pyodbc.Error as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({
                "status": "Error",
                "message": str(e)
            })
    
    try:
        # Fetch custom study sets
        cursor.execute("SELECT * FROM StudySet WHERE User_ID = ?", (username,))
        study_sets = cursor.fetchall()
        sets = []
        for study_set in study_sets:
            set_information = {
                    "set_id": study_set[1],
                    "public": study_set[3],
                    "title": study_set[4],
                    "description": study_set[5],
                    "summary": study_set[6],
                    "prompt": study_set[7],
                    "created": study_set[8]
            }
            sets.append(set_information)

        #Fetch Default Sets
        cursor.execute("Select * From StudySet Where DefaultSet = 1")
        defaultSets = cursor.fetchall()
        default_sets = []
        for default_set in defaultSets:
            tempSet = {
                "set_id": default_set[1],
                "title": default_set[4],
                "summary": default_set[6],
                "prompt": default_set[7],
                "description": default_set[5]
            }          
            default_sets.append(tempSet)      

        #Fetch Public Sets
        cursor.execute("Select * From StudySet Where PublicSet = 1")
        publicSets = cursor.fetchall()
        public_sets = []
        for public_set in publicSets:
            tempSet = {
                "user_id": public_set[0],
                "set_id": public_set[1],
                "title": public_set[4],
                "description": public_set[5],
                "summary": public_set[6],
                "prompt": public_set[7]                  
            }
            public_sets.append(tempSet)  

        cursor.execute("SELECT * FROM Users WHERE User_ID = ?", (username,))
        user = cursor.fetchone()
        pic = ""
        if user[7] is not None:
                    pic = user[7]
        else:
            pic = base64.b64encode(user[6]).decode('utf-8')

        cursor.execute("SELECT End_Date, Plan_Name FROM Subscription WHERE User_ID = ?", (username,))
        details = cursor.fetchone()
        plan = None
        if details[1] is not None:
            plan = {
                "ending": details[0],
                "name": details[1]
            }

        conn.commit() 
        cursor.close()
        conn.close()
        return jsonify({
            "status": "Valid",
            "default_sets": default_sets,
            "custom_sets": sets,
            "public_sets": public_sets,
            "pfp": pic,
            "pro": plan
        })
    
    except pyodbc.Error as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({
            "status": "Invalid",
            "message": str(e)
        })

@app.route('/update/set/statistics', methods=["POST"])
@csrf.exempt 
def update_stats_info():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    diff = float(request.form.get("diff"))
    print(diff)
    user_id = request.form.get("user_id")
    set_id = int(request.form.get("set_id"))

    try:
        query = """
        UPDATE SetStatistics
        SET Hours_Studied = Hours_Studied + ?
        WHERE User_ID = ? AND Set_ID = ?
        """
        cursor.execute(query, (diff, user_id, set_id))        
        conn.commit() 
        cursor.close()
        conn.close()

        return jsonify({
            "status": 200
        })
    
    except pyodbc.Error as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({
            "status": 500,
            "message": str(e)
        })

@app.route('/get/set/statistics', methods=["POST"])
@csrf.exempt 
def get_stats_info():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    user_id = request.form.get("user_id")
    set_id = request.form.get("set_id")

    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        query = """
        SELECT SetStatistics.*, 
            DATEDIFF(DAY,StudySet.Date_Created, CAST(GETDATE() AS DATE)) As days_completedm,
            DATEDIFF(DAY, CAST(GETDATE() AS DATE), StudySet.Test_Date) AS days_difference
        FROM SetStatistics
        JOIN StudySet ON SetStatistics.set_id = StudySet.set_id AND SetStatistics.user_id = StudySet.user_id
        WHERE SetStatistics.user_id = ? AND SetStatistics.set_id = ? 
        """
        cursor.execute(query, (user_id, set_id))
        stats = cursor.fetchone()

        if stats:
            response_data = {
                "status": 200,
                "avg_quiz": stats[2],
                "hours_studied": stats[3],
                "days_completed": stats[-2],
                "days_until_test": stats[-1]
            }
        else:
            # Fetch default set statistics if no days until test or days completed
            cursor.execute("SELECT Average_Quiz, Hours_Studied FROM SetStatistics WHERE User_ID = ? AND Set_ID = ?", (user_id, set_id))
            default_stats = cursor.fetchone()
            response_data = {
                "status": 200,
                "avg_quiz": default_stats[0] if default_stats else None,
                "hours_studied": default_stats[1] if default_stats else None
            }
        
        return jsonify(response_data)
    
    except pyodbc.Error as e:
        return jsonify({
            "status": 500,
            "message": str(e)
        })
    
    finally:
        cursor.close()
        conn.close()

#Get Default Flashcard Information 
@app.route('/default/flashcard/info', methods=["POST"])
@csrf.exempt 
def get_default_flashcard_info():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    set_id = request.form.get("set_id")
    user_id = request.form.get("user_id")

    print(set_id, user_id)

    cursor.execute("""
        IF NOT EXISTS (
            SELECT 1
            FROM UserFlashcard
            WHERE User_ID = ? AND Set_ID = ?
        )
        BEGIN
            -- Insert flashcards into UserFlashcard
            INSERT INTO UserFlashcard (User_ID, Flashcard_ID, Set_ID, Studied)
            SELECT ?, Flashcard_ID, Set_ID, 0 AS Studied
            FROM DefaultFlashcards
            WHERE Set_ID = ?;
        END
        """, (user_id, set_id, user_id, set_id))
    
    #Get flashcard info from set
    query = """
    SELECT 
    f.Flashcard_ID,
    f.Question,
    f.Answer,
    f.Option_1,
    f.Option_2,
    f.Option_3,
    uf.Studied
    FROM 
        DefaultFlashcards f
    INNER JOIN 
        UserFlashcard uf 
    ON 
        f.Flashcard_ID = uf.Flashcard_ID 
        AND f.Set_ID = uf.Set_ID
    WHERE 
        f.Set_ID = ?
        AND uf.User_ID = ?;
    """
    cursor.execute(query, (set_id, user_id))
    cards = cursor.fetchall()
    try:
        flashcards = []
        for flashcard in cards:
            options = {
                "flashcard_id": flashcard[0],
                "question": flashcard[1],
                "answer": flashcard[2],
                "option_one": flashcard[3],
                "option_two": flashcard[4],
                "option_three": flashcard[5],
                "studied": flashcard[6]
            }
            flashcards.append(options)

        conn.commit() 
        cursor.close()
        conn.close()

        thread = threading.Thread(target=create_set_statistics, args=(user_id, set_id))
        thread.start() 

        return jsonify({
            "status": "Valid",
            "flashcards": flashcards
        })
    except pyodbc.Error as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({
            "status": "Error",
            "message": str(e)
        })

@app.route('/custom/flashcard/info', methods=["POST"])
@csrf.exempt 
def get_custom_flashcard_info():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    set_id = request.form.get("set_id")
    user_id = request.form.get("user_id")
    logged_in_user_id = request.form.get("logged_in_user_id")

    if logged_in_user_id:
        cursor.execute("""
        IF NOT EXISTS (
            SELECT 1
            FROM UserFlashcard
            WHERE User_ID = ? AND Set_ID = ?
        )
        BEGIN
            -- Insert flashcards into UserFlashcard
            INSERT INTO UserFlashcard (User_ID, Flashcard_ID, Set_ID, Studied)
            SELECT ?, Flashcard_ID, Set_ID, 0 AS Studied
            FROM Flashcard
            WHERE Set_ID = ?;
        END
        """, (logged_in_user_id, set_id, logged_in_user_id, set_id))

    #Get flashcard info from set
    query = """
    SELECT 
    f.Flashcard_ID,
    f.Question,
    f.Answer,
    f.Option_1,
    f.Option_2,
    f.Option_3,
    uf.Studied
    FROM 
        Flashcard f
    INNER JOIN 
        UserFlashcard uf 
    ON 
        f.Flashcard_ID = uf.Flashcard_ID 
        AND f.Set_ID = uf.Set_ID
    WHERE 
        f.Set_ID = ?
        AND uf.User_ID = ?;
    """
    if logged_in_user_id:
        cursor.execute(query, (set_id, logged_in_user_id))
    else:
        cursor.execute(query, (set_id, user_id))

    cards = cursor.fetchall()
    try:
        flashcards = []
        for flashcard in cards:
            options = {
                "flashcard_id": flashcard[0],
                "question": flashcard[1],
                "answer": flashcard[2],
                "option_one": flashcard[3],
                "option_two": flashcard[4],
                "option_three": flashcard[5],
                "studied": flashcard[6]
            }
            flashcards.append(options)
        
        query = f"""
        SELECT T.Topic_ID, T.Topic, K.KeyPoint, K.KeyPoint_ID
        FROM Topics T
        JOIN KeyPoints K ON T.Topic_ID = K.Topic_ID
        WHERE T.User_ID = '{user_id}' AND T.Set_ID = {set_id}
        """
        cursor.execute(query)
        topics_db = cursor.fetchall()
        topics_dict = {}
        for topic_id, topic, key_point, key_point_id in topics_db:
            if topic not in topics_dict:
                topics_dict[topic] = {
                    "topic_id": topic_id,
                    "key_points": []
                }
            topics_dict[topic]["key_points"].append({
                "point": key_point,
                "point_id": key_point_id
            })

        topics = []
        for topic in topics_dict.keys():
            topics.append({
                "topic": topic,
                "id": topics_dict[topic]["topic_id"],
                "points": topics_dict[topic]["key_points"]
            })

        conn.commit() 
        cursor.close()
        conn.close()

        thread = threading.Thread(target=create_set_statistics, args=(user_id, set_id))
        thread.start() 

        return jsonify({
            "status": "Valid",
            "flashcards": flashcards,
            "topics": topics
        })
    except pyodbc.Error as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({
            "status": "Error",
            "message": str(e)
        })
    
    
def create_set_statistics(user_id, set_id):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # Create SetStatistics record for the user and set in a threat
    cursor.execute("""
    IF NOT EXISTS (
        SELECT 1 
        FROM SetStatistics 
        WHERE user_id = ? 
          AND set_id = ?
    )
    BEGIN
        INSERT INTO SetStatistics (user_id, set_id)
        VALUES (?, ?);
    END
    """, (user_id, set_id, user_id, set_id))
    
    conn.commit()
    cursor.close()
    conn.close()


@app.route('/update/flashcard/studied', methods=["POST"])
@csrf.exempt
def update_flashcard_studied():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    user_id = request.form.get("user_id")
    set_id = request.form.get("set_id")
    flashcard_id = request.form.get("flashcard_id")
    studied = int(request.form.get("studied"))
    
    try:
        query = """
        Update UserFlashcard
        Set Studied = ?
        Where User_ID = ? And Set_ID = ? And Flashcard_ID = ?
        """
        cursor.execute(query, (studied, user_id, set_id, flashcard_id))
        conn.commit() 

        return jsonify({
            "status": 200
        })

    except pyodbc.Error as e:
        print("ERROR: ", str(e))
        return jsonify({
            "status": 500,
            "message": str(e)
        })
    
    finally:
        cursor.close()
        conn.close()

@app.route('/set/flashcard/info', methods=["POST"])
@csrf.exempt 
def set_flashcard_info():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    user_id = request.form.get("user_id")
    set_id = request.form.get("set_id")
    flashcard_id = request.form.get("flashcard_id")
    type = request.form.get("type")

    try:
        if type == "existing":
            question = request.form.get("question")
            answer = request.form.get("answer")
            query = f"""
            Update Flashcard
            Set Question = ?, Answer = ?
            Where User_ID = ?
                And Set_ID = ?
                And Flashcard_ID = ?
            """
            cursor.execute(query, (question, answer, user_id, set_id, flashcard_id))
        elif type == "new":
            question = request.form.get("question")
            answer = request.form.get("answer")
            query = f"""
            Insert Into Flashcard (User_ID, Set_ID, Question, Answer)
            Values (?, ?, ?, ?)
            """
            cursor.execute(query, (user_id, set_id, question, answer))
        else:
            query = f"""
            Delete From Flashcard 
            Where User_ID = ? 
                And Set_ID = ?
                And Flashcard_ID = ?
            """
            cursor.execute(query, (user_id, set_id, flashcard_id))
        
        conn.commit() 
        return jsonify({"status": "Valid"})

    except pyodbc.Error as e:
        conn.rollback()
        return jsonify({"status": "Error", "message": str(e)})

    finally:
        cursor.close()
        conn.close()

@app.route('/users/location', methods=["POST"])
@csrf.exempt 
def get_users_in_area():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    try:
        username = request.form.get("username").lower()
        cursor.execute(f"Select Longitude, Latitude From Users where User_ID = '{username}'")
        db = cursor.fetchall()
        longitude = db[0][0] 
        latitude = db[0][1]

        radius_km = 200

        query = f"""
        SELECT Top 4 User_ID, Name, Profile_Picture, Profile_Picture_OAuth
        FROM Users
        WHERE User_ID != '{username}' AND (6371 * ACOS(
                COS(RADIANS({latitude})) * COS(RADIANS(Latitude)) *
                COS(RADIANS(Longitude) - RADIANS({longitude})) +
                SIN(RADIANS({latitude})) * SIN(RADIANS(Latitude))
            )
        ) <= {radius_km}
        Order By User_ID
        """

        cursor.execute(query)

        db = cursor.fetchall()
        email = []
        name = []
        pfp = []
        for row in db:
            email.append(row[0])
            name.append(row[1])
            if row[3] is not None:
                pfp.append(row[3])
            else:
                pfp.append(base64.b64encode(row[2]).decode('utf-8'))

        
        cursor.execute(f"Select * From [Group]")
        all_groups = cursor.fetchall()

        groups = []
        for g in all_groups:
            img = g[2]
            group = {
                "group_id": g[0],
                "group_name": g[1],
                "group_img": base64.b64encode(img).decode('utf-8'),
                "num_in_group": g[3]
            }
            groups.append(group)

        conn.commit() 
        cursor.close()
        conn.close()
        return jsonify({
            "status": "Valid",
            "names": name,
            "emails": email,
            "pfp": pfp,
            "group_info": groups,
            "longitude": longitude,
            "latitude": latitude
        })

    except pyodbc.Error as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({
            "status": "Error",
            "message": str(e)
        })

@app.route('/users/location/pagination', methods=["POST"])
@csrf.exempt 
def get_specific_users():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    try:
        username = request.form.get("user_id")
        direction = int(request.form.get("direction"))
        email = request.form.get("nav_email")
        latitude = request.form.get("latitude")
        longitude = request.form.get("longitude")
        radius_km = 161
        
        # 1 means paginate forward
        if direction == 1:
            query = f"""
            SELECT Top 4 User_ID, Name, Profile_Picture, Profile_Picture_OAuth
            FROM Users
            WHERE User_ID != '{username}' AND (6371 * ACOS(
                    COS(RADIANS({latitude})) * COS(RADIANS(Latitude)) *
                    COS(RADIANS(Longitude) - RADIANS({longitude})) +
                    SIN(RADIANS({latitude})) * SIN(RADIANS(Latitude))
                )
            ) <= {radius_km} And User_ID > '{email}'
            Order By User_ID
            """
        else:
            query = f"""
            SELECT Top 4 User_ID, Name, Profile_Picture, Profile_Picture_OAuth
            FROM Users
            WHERE User_ID != '{username}' AND (6371 * ACOS(
                    COS(RADIANS({latitude})) * COS(RADIANS(Latitude)) *
                    COS(RADIANS(Longitude) - RADIANS({longitude})) +
                    SIN(RADIANS({latitude})) * SIN(RADIANS(Latitude))
                )
            ) <= {radius_km} And User_ID < '{email}'
            Order By User_ID
            """
        
        cursor.execute(query)
        db = cursor.fetchall()
        email = []
        name = []
        pfp = []
        for row in db:
            email.append(row[0])
            name.append(row[1])
            if row[3] is not None:
                pfp.append(row[3])             
            else:
                pfp.append(base64.b64encode(row[2]).decode('utf-8'))

        return jsonify({
            "status": "Valid",
            "names": name,
            "emails": email,
            "pfp": pfp,
        })
    
    except pyodbc.Error as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({
            "status": "Error",
            "message": str(e)
        }) 

@app.route('/load/users/group', methods=["POST"])
@csrf.exempt 
def load_users_in_group():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    try: 
        group_id = request.form.get('group_id')
        direction = int(request.form.get("direction"))
        users = []
        user_info = None

        if direction == 0:
            query = f"""
            Select Top 5 User_ID, [Name]
            From UsersInGroup
            Where Group_ID = {group_id}
            Order By User_ID
            """
            cursor.execute(query)
            user_info = cursor.fetchall()        
        # 1 means paginate forward
        elif direction == 1:
            navigation_email = request.form.get("navigationEmail")
            query = """
            SELECT TOP 5 User_ID, [Name]
            FROM UsersInGroup
            WHERE Group_ID = ? AND User_ID > ?
            ORDER BY User_ID
            """
            cursor.execute(query, (group_id, navigation_email))
            user_info = cursor.fetchall()
            
        for user in user_info:
            cursor.execute(f"Select Profile_Picture, Profile_Picture_OAuth From Users Where User_ID = '{user[0]}'")
            curr_user = cursor.fetchone()
            pic = ""
            if curr_user[1] is not None:
                pic = curr_user[1]
            else:
                pic = base64.b64encode(curr_user[0]).decode('utf-8')
            temp_user = {
                "email": user[0],
                "name": user[1],
                "pfp": pic
            }
            users.append(temp_user)
        conn.commit() 
        cursor.close()
        conn.close()
        return jsonify({
            "status": "Valid",
            "users_in_group": users 
        })
    except pyodbc.Error as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({
            "status": "Error",
            "message": str(e)
        })

@app.route('/add/groups', methods=["POST"])
@csrf.exempt 
def add_to_group():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    user_id = request.form.get("email").lower()
    name = request.form.get("name")
    group_id = request.form.get("group_id")
    try: 
        validate_query = f"Select * From [UsersInGroup] Where Group_ID = {group_id} AND User_ID = '{user_id}' "
        cursor.execute(validate_query)
        if cursor.fetchone():
            return jsonify({
                "status": "Error",
                "message": "User already in group"
            })

        insert_query = f"INSERT INTO [UsersInGroup] (User_ID, Group_ID, [Name]) VALUES ('{user_id}', {group_id}, '{name}')"
        cursor.execute(insert_query)

        update_query = f"UPDATE [Group] SET Number_Of_Users = Number_Of_Users + 1 WHERE Group_ID = {group_id}"
        cursor.execute(update_query)

        conn.commit() 
        cursor.close()
        conn.close()
        return jsonify({
            "status": "Valid"
        })
    except pyodbc.Error as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({
            "status": "Error",
            "message": str(e)
        })

@app.route('/leave/group', methods=["POST"])
@csrf.exempt
def leave_group():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    user_id = request.form.get("email")
    group_id = request.form.get("group_id")

    try: 
        cursor.execute(f"Delete From UsersInGroup Where User_ID = '{user_id}' And Group_ID = {group_id}")
        deleted = cursor.rowcount
        if deleted > 0:
            cursor.execute(f"Update [Group] Set Number_Of_Users = Number_Of_Users - 1 Where Group_ID = {group_id}")

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "status": "Valid"
        })
    
    except pyodbc.Error as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({
            "status": "Error",
            "message": str(e)
        })

#Change set visibility 
@app.route('/update/set/visibility', methods=["POST"])
@csrf.exempt
def change_set_visibility():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    public = int(request.form.get("public"))
    user_id = request.form.get("user_id")
    set_id = request.form.get("set_id")

    try:
        cursor.execute(f"Update StudySet Set PublicSet = {public} Where User_ID = '{user_id}' and Set_ID = {set_id}")
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "status": 200
        })
    
    except pyodbc.Error as e:
        conn.rollback()
        cursor.close()
        conn.close()

        return jsonify({
            "status": 500,
            "message": str(e)
        })
    
@app.route('/set/topics', methods=["POST"])
@csrf.exempt
def set_topics():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    #update topic (1) or keypoint (0)
    type = int(request.form.get("type"))

    user_id = request.form.get("user_id")
    topic_id = request.form.get("topic_id")
    set_id = request.form.get("set_id")
    text = request.form.get("text")
    try:
        #1 == topic
        if type == 1:
            query = f"""
            Update Topics 
            Set Topic = ?
            Where Topic_ID = ?
                And Set_ID = ?
                And User_ID = ?
            """
            cursor.execute(query, (text, topic_id, set_id, user_id))
        else:
            keypoint_id = request.form.get("keypoint_id")
            query = f"""
            UPDATE KeyPoints 
            SET KeyPoint = ?
            WHERE Topic_ID = ?
            AND Set_ID = ?
            AND User_ID = ?
            AND KeyPoint_ID = ?
            """
            cursor.execute(query, (text, topic_id, set_id, user_id, keypoint_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        #200
        return jsonify({
            "status": "Valid"
        })
    except pyodbc.Error as e:
        conn.rollback()
        cursor.close()
        conn.close()
        #500
        return jsonify({
            "status": "Error",
            "message": str(e)
        })

# get the last message and user info for every user who has sent or recieved a message to current user
@app.route('/get/all/messages', methods=["POST"])
@csrf.exempt
def get_all_messages():
    recipient_id = request.form.get("user_id")
    intended_user = request.form.get("intended_user")
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    try: 
        intend = None
        if intended_user is not None:
            cursor.execute(f"Select * From Users Where User_ID = '{intended_user}'")
            intended = cursor.fetchone()
            pic = ""
            if intended[7] is not None:
                pic = intended[7]
            else:
                pic = base64.b64encode(intended[6]).decode('utf-8')

            intend = {
                "name": intended[5],
                "email": intended[0],
                "pfp": pic,
                "last_login": intended[4]
            }

        #get last message too
        query = f"""
        SELECT m.CommunicationPartner,
            m.LastMessageID,
            msg.Message_Content AS LastMessage
        FROM (
            SELECT CASE
                    WHEN Sender_ID = '{recipient_id}' THEN Recipient_ID
                    ELSE Sender_ID
                END AS CommunicationPartner,
                MAX(Message_ID) AS LastMessageID
            FROM Message
            WHERE Recipient_ID = '{recipient_id}' OR Sender_ID = '{recipient_id}'
            GROUP BY CASE
                        WHEN Sender_ID = '{recipient_id}' THEN Recipient_ID
                        ELSE Sender_ID
                    END
        ) AS m
        JOIN Message AS msg
        ON m.LastMessageID = msg.Message_ID
        ORDER BY m.LastMessageID DESC;
        """
        cursor.execute(query)
        users = cursor.fetchall()
        all_users = []
        for user in users:
            cursor.execute(f"Select * From Users Where User_ID = '{user[0]}'")
            specific_user = cursor.fetchone()
            pic = ""
            if specific_user[7] is not None:
                pic = specific_user[7]
            else:
                pic = base64.b64encode(specific_user[6]).decode('utf-8')

            all_users.append({
                "name": specific_user[5],
                "email": specific_user[0],
                "pfp": pic,
                "last_login": specific_user[4],
                "last_message": user[2]
            })

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "status": "Valid",
            "users": all_users,
            "intended": intend
        })

    except pyodbc.Error as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({
            "status": "Error",
            "message": str(e)
        })

@app.route('/get/user/messages', methods=["POST"])
@csrf.exempt
def get_user_messages():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    user_id = request.form.get("user_id")
    recipient_id = request.form.get("recipient_id")
    try:
        query = f"""
        SELECT Message_ID, Sender_ID, Time, Message_Content, IsRead 
        FROM Message WITH (NOLOCK)
        WHERE (Sender_ID = '{user_id}' AND Recipient_ID = '{recipient_id}') 
        OR (Sender_ID = '{recipient_id}' AND Recipient_ID = '{user_id}')
        Order By Message_ID asc        
        """
        cursor.execute(query)
        messages_db = cursor.fetchall()
        messages = []
        for m in messages_db:
            messages.append({
                "message_id": m[0],
                "sender": m[1],
                "time_sent": m[2],
                "message": m[3],
                "read": m[4]
            })

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({
            "status": "Valid",
            "messages": messages
        })
    except pyodbc.Error as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({
            "status": "Error",
            "message": str(e)
        })

@app.route('/set/notes', methods=["POST"])
@csrf.exempt
def set_notes():
    new_text = request.form.get("text")
    user_id = request.form.get("user_id")
    set_id = int(request.form.get("set_id"))
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    try:
        sql = f"UPDATE StudySet SET Summary = ? WHERE User_ID = ? AND Set_ID = ?"
        cursor.execute(sql, (new_text, user_id, set_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({
            "status": "Valid"
        })
    except pyodbc.Error as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({
            "status": "Error",
            "message": str(e)
        })

@app.route('/report/message', methods=["POST"])
@csrf.exempt
def report_message():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    message_content = request.form.get("messageContent")
    reporter_id = request.form.get("reporterID")
    reported_id = request.form.get("reportedID")

    if request.form.get("reason") is not None:
        reason = request.form.get("reason") 
    else:
        reason = "No reason provided"

    if request.form.get("messageID") is not None: 
        message_id = request.form.get("messageID") 
    else:
        cursor.execute(f"Select Message_ID From Message Where Sender_ID = {reported_id} and RecipientID = {reporter_id} and Message_Content = {message_content}")
    
    try:
        report_message = """
        INSERT INTO ReportMessage (ReporterID, ReportedID, MessageContent, MessageID, Reason)
        VALUES (?, ?, ?, ?, ?);
        """
        cursor.execute(report_message, (reporter_id, reported_id, message_content, message_id, reason))

        # Get the total number of reports for the reported user. returns tuple => (user_id, count)
        count_sql = """
        SELECT ReportedID, COUNT(*) AS ReportCount
        FROM ReportMessage
        WHERE ReportedID = ?
        GROUP BY ReportedID;
        """
        cursor.execute(count_sql, (reported_id,))
        report_count = cursor.fetchone()

        cursor.execute(f"Delete From Message Where Message_ID = {message_id}")
       
        conn.commit()
        cursor.close()
        conn.close()
        
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        email_content = f"""
        <html>
        <head></head>
        <body>
            <h2>REPORT ALERT</h2>
            <p><strong>{reporter_id}</strong> reported <strong>{reported_id}</strong></p>
            <p><strong>Message: </strong>"{message_content}"</p>
            <p><strong>Reason: </strong><em>{reason}</em></p>
            <p><strong>Number of Reports:</strong>{report_count}</p>
            <p><strong>Date: </strong>{current_datetime}</p>
        </body>
        </html>
        """        
        thread = threading.Thread(target=send_email, args=(f"Message Report - {reporter_id} reported {reported_id}", email_content, ["quizmereports@gmail.com"]))
        thread.start()        
        return jsonify({
            "status": "Valid"
        })
    except pyodbc.Error as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({
            "status": "Error",
            "message": str(e)
        })

@app.route('/contact/us', methods=["POST"])
@csrf.exempt
def contact_us():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    name = request.form.get('name')
    email = request.form.get('email')
    description = request.form.get('description')

    cursor.execute(f"Select * From Users Where User_ID = ?", (email,))
    userExists = cursor.fetchone()

    if userExists:
        email_content = f"""
        <html>
        <head></head>
        <body>
            <h2>User Contact</h2>
            <p>Name: <strong>{name}</strong></p>
            <p>Email: <strong>{email}</strong></p>
            <p>Message: {description}</em></p>
        </body>
        </html>
        """   
        
        try:
            query = f"""
            Insert Into ContactUs (User_ID, Message)
            Values (?, ?)
            """
            cursor.execute(query, (email, description))
            conn.commit()
            cursor.close()
            conn.close()
        except pyodbc.Error as e:
            conn.rollback()
            cursor.close()
            conn.close()
            return jsonify({
                "status": 500,
                "message": str(e)
            })
        
        thread = threading.Thread(target=send_email, args=(f"User Contact - {name} - {email}", email_content, ["quizmereports@gmail.com", email]))
        thread.start()   
        return jsonify({
            "status": "Valid"
        })
    else:
        return jsonify({
            "status": 404,
            "message": f"User with email {email} does not exist"
        })
    
@app.route('/delete/message', methods=["POST"])
@csrf.exempt
def delete_message():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    message_id = request.form.get("messageID")

    try:
        cursor.execute(f"Delete From Message Where Message_ID = {message_id}")
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "status": "Valid"
        })
    except pyodbc.Error as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({
            "status": "Error",
            "message": str(e)
        })


@app.route('/join/early/access', methods=["POST"])
@csrf.exempt
def join_early_access():
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    fullName = request.form.get("fullName")
    email = request.form.get("email")

    email_content = f"""
        <html>
        <head></head>
        <body>
            <p>hey {fullName},</p>
            <p>we got your info!</p>
            <p>while we keep building, feel free to reach out to us with any questions!</p>
            <p>thanks for joining and good luck this semester!</p>
            <p>- kevin roy<p>
            <br></br>
            <p>in the meantime follow our socials to keep up with dates and giveaways!</p>
            <a href="https://www.linkedin.com/company/quizmeai" target="_blank">LinkedIn</a><br>
            <a href="https://www.instagram.com/revixai/" target="_blank">Instagram</a>
        </body>
        </html>
        """   
    
    try:
        query = """
        MERGE INTO EarlyAccessUsers AS target
        USING (SELECT ? AS FullName, ? AS Email) AS source
        ON target.Email = source.Email
        WHEN NOT MATCHED BY TARGET THEN
            INSERT (FullName, Email)
            VALUES (source.FullName, source.Email)
        OUTPUT $action AS MergeAction;
        """
        cursor.execute(query, (fullName, email))
        result = cursor.fetchone()

        if not result:
            return jsonify({
                "status": 500,
                "message": "Looks like there's already an account with this email. If this was a mistake please contact us!"
            })
        
        conn.commit()
        cursor.close()
        conn.close()
        thread = threading.Thread(target=send_email, args=(f"Welcome to Revix AI!", email_content, [email]))
        thread.start()

        return jsonify({
            "status": 200,
            "message": "It's official - you're in!"
        })
        
    except pyodbc.Error as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({
            "status": 500,
            "message": "Looks like something went wrong - try one more time, if it keeps failing contact us!"
        })

def send_email(subject, text_content, emails):
    # Start connection
    my_server = smtplib.SMTP(gmail_server, gmail_port)
    my_server.ehlo()
    my_server.starttls()

    # Login with quizme email and password
    my_server.login(quizme_email, quizme_password)
    
    for i in range(len(emails)):
        # Create a new MIMEMultipart message for each recipient
        message = MIMEMultipart("alternative")
        message['Subject'] = subject
        message['From'] = quizme_email
        message['To'] = emails[i]

        message.attach(MIMEText(text_content, "html"))

        # Convert the message to a string
        message_str = message.as_string()

        my_server.sendmail(
            from_addr=quizme_email,
            to_addrs=emails[i],
            msg=message_str
        )

    my_server.quit()

@app.route('/summary', methods=["POST"])
@csrf.exempt
def summary():
    summary_type = int(request.form.get('type'))
    points = {}
    title = request.form.get('title')
    user_id = request.form.get('user_id')
    description = request.form.get('description')
    subject = request.form.get('subject')

    #pdf
    if summary_type == 0:
        text = ''
        reader = PyPDF2.PdfReader(request.files['pdf'])
        for page in reader.pages:
            page_text = page.extract_text()
            lines = page_text.split('\n')
            # Join lines to form paragraphs
            formatted_text = ' '.join(lines)
            text += formatted_text
        points = get_notes(text, subject, user_id, title)
    
    # yt link
    elif summary_type == 1:
        return jsonify({'type': "id"})
        transcript = YouTubeTranscriptApi.get_transcript(request.form.get('yt'))
        notes = ""
        for t in transcript:
            hold = t['text'] + " "
            notes += hold
        
        #summary = summarize(notes)
        points["prompt"] = notes
        # return jsonify(summary)
    
    # recording
    elif summary_type == 2:
        return jsonify({'type': "notes"})

    # pasted notes
    else:
        return jsonify({'type': "else"})
        NOTES = request.form.get('notes')
        #summary = summarize(NOTES)
        points["prompt"] = NOTES
        # return jsonify(summary)

    return jsonify({'points': points})

class Topic(BaseModel):
    name: str
    points: List[str]

class AllTopics(BaseModel):
    topics: List[Topic]


def get_notes(content, subject, user_id, title):
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    if subject == "Other":
        subject = ""
    try: 
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": f"You area a tutor that creates concise notes based on minimum 3 - 8 specific topics derived from the text's content, and extract key points for each topic. The number of topics should be determined based on the text's length and relevance. Output the results in JSON"
                    f"The JSON object must use the schema: {json.dumps(AllTopics.model_json_schema(), indent=2)}."
                },
                {
                    "role": "user",
                    "content": f"Fetch the topic and key points from this text: {content}",               
                }
            ],
            model="llama3-8b-8192",
            stream=False,
            temperature=0,
            response_format={"type": "json_object"}
        )
        print(chat_completion.choices[0].message.content)
        validated = AllTopics.model_validate_json(chat_completion.choices[0].message.content)
        print("VALIDATED: ", validated)
        topics = []
        for note in validated.topics:
            print("NOTE: ", note.name)
            print("POINTS: ", note.points)
            tool = YouTubeSearchTool()
            try:
                link = tool.run(f"{title} {note.name}, 1")
            except Exception as e:
                link = tool.run(f"{title}, 1")

            print("LINK: ", link)
            topic = {
                "name": note.name,
                "points": note.points,
                "link": link
            }
            topics.append(topic)
        
        print("TOPICS ARRAY: ", topics)
       # cursor.execute("")

        return topics

    except Exception as e:
        print(str(e))
        return {
            "status": "error",
            "error": str(e)
        }

    """
    name:  History of Soccer
    points:
    Ancient civilizations such as the Chinese, Greeks, Romans, and Egyptians played ball games resembling soccer as early as 200 BC.  
    Medieval England saw the development of soccer as a distinct sport, with matches held between neighboring villages and towns.     
    The Football Association was established in 1863, marking the birth of modern soccer.
    Soccer has since grown into a global phenomenon, captivating billions of fans worldwide.
    """


def summarize(prompt):
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers = {
        "Authorization": f"Bearer {hugging_face}"
    }

    def query(payload):
        response = requests.post(API_URL, headers=headers, json=payload)
        return response.json()
    
    try:
        output = query({
            "inputs: ": prompt,
        })
        print(output)
        summary = {"summary": output}

    except KeyError as e:
        summary = {
            "Status": "Error",
            "Message": str(e)
        }

    #keywords = get_keywords(output["summary_text"])
    #summary["keywords"] = keywords

    return summary

def get_keywords(summary):
    API_URL = "https://api-inference.huggingface.co/models/yanekyuk/bert-keyword-extractor"
    headers = {"Authorization": f"Bearer {hugging_face}"}
    def query(payload):
        response = requests.post(API_URL, headers=headers, json=payload)
        return response.json()
        
    output = query({
        "inputs": summary,
    })

    return output

@app.route('/quiz', methods=["POST"])
@csrf.exempt
def create_quiz():
    prompt = request.form.get("prompt")
    numQuestions = request.form.get("numQuestions")
    numQuestions = 2
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"You are a teacher who generates {numQuestions} quiz questions based on a text. Each question has 4 answer choices. Make the first answer choice for each question the correct answer. Seperate each question with a dollar sign ($). Here is an example => Question 1: Who is Ronaldo?  A) A soccer player B) A basketball player C) A cricket player D) A scientist  $ Question 2: What is the capital of France? A) Paris B) Baltimore C) Moscow D) Italy $"},
            {"role": "user", "content": prompt}
        ]
    )
    quiz_text = response["choices"][0]["message"]["content"].split("$")
    quiz = {
        'quiz_questions': quiz_text
    }
    return quiz