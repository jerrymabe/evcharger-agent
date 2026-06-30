import uuid, sqlite3
from datetime import datetime
import config as settings

class Session:
    def __init__(self, conn = None, cursor = None):
        self.conn = conn if conn else sqlite3.connect(settings.DB_NAME)
        self.cursor = cursor if conn else self.conn.cursor()

    def get_sessions(self, user_id:str):
        read_query = "SELECT session_id, title FROM session WHERE user_id = '"+user_id+"' AND is_active = 1 ORDER BY start_time DESC"
        self.cursor.execute(read_query)
        session_list = self.cursor.fetchall()
        print("No. of sessions: ",len(session_list))
        return session_list

    def create_new_session(self, user_id:str, title:str):
        session_id = str(uuid.uuid4())
        data_to_insert = (session_id,user_id,title,str(datetime.now()))
        insert_query = "INSERT INTO session (session_id, user_id, title, start_time, request_count, is_active) VALUES (?, ?, ?, ?, 0, 1)"
        self.cursor.execute(insert_query, data_to_insert)
        self.conn.commit()
        return session_id
    
    def get_latest_session(self):
        read_query = "SELECT session_id FROM session ORDER BY start_time DESC LIMIT 1"
        self.cursor.execute(read_query)
        session = self.cursor.fetchall()[0][0]
        return session
    
    def get_history(self, session_id:str):
        read_history = "SELECT user_query, llm_response FROM session_history WHERE session_id = '"+session_id+"' ORDER BY history_id"
        self.cursor.execute(read_history)
        history = self.cursor.fetchall()
        return history
    
    def update_session(self, session_id:str):
        update_session = "UPDATE session SET request_count = request_count + 1 WHERE session_id = '"+session_id+"'"
        self.cursor.execute(update_session)
        self.conn.commit()
        return "success"

    def update_feedback(self, feedback:int):
        update_session = "UPDATE session_history SET feedback = "+str(feedback)+" WHERE history_id = (SELECT MAX(history_id) FROM session_history)"
        self.cursor.execute(update_session)
        self.conn.commit()
        return "success"
    
    def write_history(self, session_id:str, user_query:str, rephrased_query:str, llm_response:str, response_time:float):
        data_to_insert = (session_id, user_query, rephrased_query, llm_response, str(datetime.now()), response_time)
        insert_query = "INSERT INTO session_history (session_id, user_query, rephrased_query, llm_response, time_stamp, response_time) VALUES (?, ?, ?, ?, ?, ?)"
        self.cursor.execute(insert_query, data_to_insert)
        self.conn.commit()
        return self.cursor.lastrowid