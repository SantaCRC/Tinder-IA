# Tinder Bot Powered by AI

This bot automates swiping on Tinder using AI. It is for educational purposes only and is not endorsed by Tinder.

## Motivation

This project is a hobby initiative to explore the potential of AI in learning and mimicking human preferences. The goal is to see how effectively an AI can learn about a person's likes and dislikes, making informed decisions while swiping on Tinder.

## Features

- [x] Auto-Swiping right on Tinder
- [x] Auto-Swiping left on Tinder
- [x] Display last liked and last passed images
- [x] Console output redirected to GUI
- [x] Thread-safe operations for smooth GUI interaction
- [ ] Messaging on Tinder
- [ ] Matching on Tinder
- [ ] Super liking on Tinder
- [ ] Auto-login

## Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/SantaCRC/Tinder-IA.git
   ```
2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
3. **Run the bot:**
   ```sh
   python main.py
   ```

If it is your first time running the bot, it will create a `.env` file and run an authentication process.

## Usage

The first time you run the bot, if no model is found, it will start training a new model. This process can take a few minutes, depending on your hardware. After the model is trained, the bot will start swiping on Tinder.

### Login Process

1. **Authentication:**
   - If no authentication tokens are found, the bot will guide you through the login process.
   - Enter your phone number when prompted.
   - Check your phone for the OTP and enter it when asked.
   - If email verification is required, check your email and enter the code.
   - The bot will save the authentication tokens in the `.env` file for future use.

### Running the Bot

- Once the bot is running, it will continuously swipe right or left based on the AI model's predictions.
- The GUI will display the last liked and last passed images.
- Console outputs, including error messages and status updates, will be displayed in the GUI for easy monitoring.

### Stopping the Bot

- Use the "Stop Tinder Bot" button in the GUI to stop the bot safely.
- The bot will complete the current operation and then stop.

## Disclaimer

This project is for educational purposes only. Use it responsibly and at your own risk. The author is not responsible for any misuse of this software.