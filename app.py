import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import time
from streamlit.runtime.scriptrunner import get_script_run_ctx

def get_user_id():
    """Generate a unique identifier for each user based on their session info"""
    ctx = get_script_run_ctx()
    if ctx is None:
        return None
    return hash(f"{ctx.session_id}")

# Database setup
def init_db():
    conn = sqlite3.connect('votes.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS votes
        (vote_id TEXT PRIMARY KEY,
         user_id TEXT,
         vote TEXT,
         timestamp DATETIME)
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS active_sessions
        (session_id TEXT PRIMARY KEY,
         stock_name TEXT,
         trade_type TEXT,
         num_shares INTEGER,
         end_time DATETIME)
    ''')
    conn.commit()
    conn.close()

def record_vote(vote):
    user_id = get_user_id()
    conn = sqlite3.connect('votes.db')
    c = conn.cursor()
    
    # Check if user already voted
    c.execute('SELECT * FROM votes WHERE user_id = ? AND vote_id = ?', 
             (user_id, st.session_state.vote_id))
    if c.fetchone() is None:
        c.execute('INSERT INTO votes VALUES (?, ?, ?, ?)',
                 (st.session_state.vote_id, user_id, vote, datetime.now()))
        conn.commit()
        st.session_state.has_voted = True
        st.success('Vote recorded!')
    else:
        st.error('You have already voted!')
    conn.close()

def get_vote_counts():
    conn = sqlite3.connect('votes.db')
    c = conn.cursor()
    c.execute('''
        SELECT vote, COUNT(*) 
        FROM votes 
        WHERE vote_id = ? 
        GROUP BY vote''', (st.session_state.vote_id,))
    results = dict(c.fetchall())
    conn.close()
    return results.get('Yes', 0), results.get('No', 0)

# Initialize database on first run
init_db()

# Initialize session state variables
if 'voting_active' not in st.session_state:
    st.session_state.voting_active = False
if 'votes_yes' not in st.session_state:
    st.session_state.votes_yes = 0
if 'votes_no' not in st.session_state:
    st.session_state.votes_no = 0
if 'voted_users' not in st.session_state:
    st.session_state.voted_users = set()
if 'end_time' not in st.session_state:
    st.session_state.end_time = None
# Add new session state variables for voting details
if 'stock_name' not in st.session_state:
    st.session_state.stock_name = ""
if 'trade_type' not in st.session_state:
    st.session_state.trade_type = "BUY"
if 'num_shares' not in st.session_state:
    st.session_state.num_shares = 100
# Add new session state variable for user's vote status
if 'has_voted' not in st.session_state:
    st.session_state.has_voted = False
# Add new session state variable for countdown
if 'countdown_active' not in st.session_state:
    st.session_state.countdown_active = False
if 'countdown_start' not in st.session_state:
    st.session_state.countdown_start = None

def start_voting(stock_name, trade_type, num_shares, duration_minutes):
    if not stock_name:
        st.error('Please enter a stock ticker!')
        return
        
    st.session_state.countdown_active = True
    st.session_state.countdown_start = datetime.now()
    st.session_state.stock_name = stock_name
    st.session_state.trade_type = trade_type
    st.session_state.num_shares = num_shares
    st.session_state.duration = duration_minutes

def start_actual_voting():
    st.session_state.countdown_active = False
    st.session_state.voting_active = True
    st.session_state.end_time = datetime.now() + timedelta(minutes=st.session_state.duration)
    st.session_state.votes_yes = 0
    st.session_state.votes_no = 0
    st.session_state.voted_users = set()

def reset_voting_session():
    """Reset all session state variables for a new vote"""
    st.session_state.voting_active = False
    st.session_state.countdown_active = False
    st.session_state.votes_yes = 0
    st.session_state.votes_no = 0
    st.session_state.voted_users = set()
    st.session_state.end_time = None
    st.session_state.stock_name = ""
    st.session_state.trade_type = "BUY"
    st.session_state.num_shares = 100
    st.session_state.has_voted = False
    st.session_state.countdown_start = None

def main():
    # Add logo in upper left corner
    st.markdown("""
        <style>
        [data-testid="stSidebarContent"] {
            padding-top: 180px;  /* Further increased padding */
        }
        [data-testid="stImage"] {
            position: relative;  /* Changed from fixed to relative */
            z-index: 999;
            padding: 10px;
            background: transparent;
            margin-top: 60px;  /* Further increased margin */
        }
        .main {
            background-color: #1E1E1E;
            color: #FFFFFF;
            padding-top: 60px;  /* Further increased padding */
        }
        .stButton>button {
            color: #FFFFFF;
            background-color: #FF9800;
            border: none;
            border-radius: 4px;
            padding: 10px 24px;
        }
        .stButton>button:hover {
            background-color: #F57C00;
        }
        .vote-no>button {
            background-color: #FF0000 !important;
        }
        .vote-no>button:hover {
            background-color: #D32F2F !important;
        }
        /* Add orange border to stock ticker input */
        [data-testid="stTextInput"] input {
            border: 2px solid #FF9800 !important;
            border-radius: 4px;
        }
        [data-testid="stTextInput"] input:focus {
            border-color: #F57C00 !important;
            box-shadow: 0 0 0 2px rgba(255, 152, 0, 0.2);
        }
        </style>
    """, unsafe_allow_html=True)

    # Create a container for the logo
    logo_container = st.container()
    with logo_container:
        st.image("https://media.licdn.com/dms/image/v2/C560BAQGPoRhVnpAkgg/company-logo_200_200/company-logo_200_200/0/1630648564615/lonebull_enterprises_logo?e=1747872000&v=beta&t=GgyfiWJdMqHihvZjrQbbiyQTDRKRMIpNYtxmEa2Jq1k", 
                width=120)

    # Add even more space after the logo
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    st.title('RIT FMA | Stock Pitch Voting Poll')
    
    # Generate a unique session ID for each user
    if 'session_id' not in st.session_state:
        st.session_state['session_id'] = str(datetime.now())

    # Start voting section
    if not st.session_state.voting_active and not st.session_state.countdown_active:
        st.header('Start New Vote')
        
        with st.form("voting_form"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                stock_name = st.text_input('Enter Stock Ticker:').upper()
            
            with col2:
                trade_type = st.selectbox(
                    'Select Trade Type:',
                    options=['BUY', 'SELL']
                )
            
            with col3:
                num_shares = st.number_input(
                    'Number of Shares:',
                    min_value=1,
                    max_value=1000000,
                    value=100,
                    step=100
                )
            
            with col4:
                seconds = st.number_input('Duration (seconds):',
                                      min_value=10,
                                      max_value=300,
                                      value=60)
            
            
            submitted = st.form_submit_button('Click/Tap twice to start voting')
            if submitted and stock_name:
                duration = seconds / 60  # Convert to minutes for internal use
                start_voting(stock_name, trade_type, num_shares, duration)

    # Countdown section
    elif st.session_state.countdown_active:
        st.empty()  # Clear previous content
        
        time_elapsed = (datetime.now() - st.session_state.countdown_start).total_seconds()
        countdown_seconds = 3
        
        if time_elapsed >= countdown_seconds:
            start_actual_voting()
            st.rerun()
        else:
            remaining = countdown_seconds - int(time_elapsed)
            st.markdown(f"<h1 style='text-align: center; color: red;'>Voting will begin in {remaining}...</h1>", unsafe_allow_html=True)
            time.sleep(1)
            st.rerun()

    # Active voting section
    elif st.session_state.voting_active:
        st.header(f'Active Vote: {st.session_state.trade_type} {st.session_state.num_shares:,} shares of {st.session_state.stock_name}')
        
        # Check if voting period has ended
        if datetime.now() > st.session_state.end_time:
            st.session_state.voting_active = False
        else:
            # Display time remaining
            time_remaining = st.session_state.end_time - datetime.now()
            minutes_remaining = time_remaining.seconds // 60
            seconds_remaining = time_remaining.seconds % 60
            st.write(f'Time remaining: {minutes_remaining}m {seconds_remaining}s')
            
            # Only show voting buttons if user hasn't voted
            if not st.session_state.has_voted:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button('Vote Yes'):
                        record_vote('Yes')
                with col2:
                    if st.button('Vote No'):
                        record_vote('No')
            else:
                st.info('Thank you for voting! Please wait for final results.')
            
            # Force rerun every second to update timer
            time.sleep(1)
            st.rerun()

    # Display final results
    if not st.session_state.voting_active and st.session_state.end_time and datetime.now() > st.session_state.end_time:
        st.header('Final Results')
        total_votes = st.session_state.votes_yes + st.session_state.votes_no
        if total_votes > 0:
            yes_percentage = (st.session_state.votes_yes / total_votes) * 100
            no_percentage = (st.session_state.votes_no / total_votes) * 100
            st.write(f'Yes Votes: {st.session_state.votes_yes} ({yes_percentage:.1f}%)')
            st.write(f'No Votes: {st.session_state.votes_no} ({no_percentage:.1f}%)')
            st.write(f'Total Votes: {total_votes}')
        else:
            st.write('No votes were recorded.')
        
        # Add button to start new vote
        if st.button('Start New Vote'):
            reset_voting_session()
            st.rerun()

if __name__ == '__main__':
    main()