from flask import Flask, render_template, request, jsonify, session
import sqlite3
import random

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Ensure you set a secret key
DATABASE = 'casino.db'


# Database setup
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE,
                            balance INTEGER DEFAULT 1000
                        )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS history (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            user_id INTEGER,
                            game TEXT,
                            result TEXT,
                            amount INTEGER,
                            FOREIGN KEY(user_id) REFERENCES users(id)
                        )''')


def create_deck():
    """Creates a standard deck of cards."""
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'jack', 'queen', 'king', 'ace']
    suits = ['hearts', 'diamonds', 'clubs', 'spades']
    return [{'rank': rank, 'suit': suit} for rank in ranks for suit in suits]


def calculate_hand_value(hand):
    """Calculates the value of a Blackjack hand."""
    value = 0
    aces = 0
    for card in hand:
        if card['rank'].isdigit():
            value += int(card['rank'])
        elif card['rank'] in ['jack', 'queen', 'king']:
            value += 10
        else:  # Ace
            aces += 1

    # Add aces as 11 first, then adjust if needed
    for _ in range(aces):
        if value + 11 > 21:
            value += 1
        else:
            value += 11

    return value


def is_soft_hand(hand):
    """Check if the hand is a soft hand (contains an Ace valued as 11)."""
    return any(card['rank'] == 'ace' for card in hand) and calculate_hand_value(hand) <= 17


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/blackjack', methods=['GET', 'POST'])
def blackjack():
    if request.method == 'POST':
        action = request.json.get('action', None)
        session = request.json.get('session', None)

        if not session or action == 'new_game':
            deck = create_deck()
            random.shuffle(deck)
            player_hand = [deck.pop(), deck.pop()]
            dealer_hand = [deck.pop(), deck.pop()]
            session = {'deck': deck, 'player_hand': player_hand, 'dealer_hand': dealer_hand}

        else:
            deck = session['deck']
            player_hand = session['player_hand']
            dealer_hand = session['dealer_hand']

        if action == 'hit':
            player_hand.append(deck.pop())
            if calculate_hand_value(player_hand) > 21:
                return jsonify({'result': 'bust', 'session': session, 'player_hand': player_hand, 'dealer_hand': dealer_hand})

        if action == 'stand':
            while calculate_hand_value(dealer_hand) < 17 or (is_soft_hand(dealer_hand) and calculate_hand_value(dealer_hand) == 17):
                dealer_hand.append(deck.pop())

            player_total = calculate_hand_value(player_hand)
            dealer_total = calculate_hand_value(dealer_hand)

            if dealer_total > 21 or player_total > dealer_total:
                return jsonify({'result': 'win', 'session': session, 'player_hand': player_hand, 'dealer_hand': dealer_hand})
            elif player_total < dealer_total:
                return jsonify({'result': 'lose', 'session': session, 'player_hand': player_hand, 'dealer_hand': dealer_hand})
            else:
                return jsonify({'result': 'push', 'session': session, 'player_hand': player_hand, 'dealer_hand': dealer_hand})

        return jsonify({'session': session, 'player_hand': player_hand, 'dealer_hand': dealer_hand})

    return render_template('blackjack.html')


@app.route('/refresh_game', methods=['POST'])
def refresh_game():
    """Resets the game state by reshuffling the deck and dealing new cards."""
    deck = create_deck()
    random.shuffle(deck)
    player_hand = [deck.pop(), deck.pop()]
    dealer_hand = [deck.pop(), deck.pop()]
    session = {'deck': deck, 'player_hand': player_hand, 'dealer_hand': dealer_hand}
    return jsonify({'session': session, 'player_hand': player_hand, 'dealer_hand': dealer_hand})


@app.route('/roulette', methods=['GET', 'POST'])
def roulette():
    if request.method == 'POST':
        bet = int(request.form['bet'])
        chosen_color = request.form['color']
        winning_color = random.choice(['red', 'black'])

        if chosen_color == winning_color:
            payout = bet * 2
            result = "win"
        else:
            payout = 0
            result = "lose"

        return jsonify({'result': result, 'winning_color': winning_color, 'payout': payout})

    return render_template('roulette.html')


@app.route('/slots', methods=['GET', 'POST'])
def slots():
    if request.method == 'POST':
        symbols = ['🍒', '🔔', '7️⃣', '⭐', '🍋']
        result = [random.choice(symbols) for _ in range(3)]
        if len(set(result)) == 1:
            payout = 100
            game_result = "win"
        else:
            payout = 0
            game_result = "lose"
        return jsonify({'result': game_result, 'symbols': result, 'payout': payout})
    return render_template('slots.html')


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
