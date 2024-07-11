# Tinder Bot Powered by AI

This bot automates swiping on Tinder using AI. It is for educational purposes only and is not endorsed by Tinder.

## Motivation

This project is a hobby initiative to explore the potential of AI in learning and mimicking human preferences. The goal is to see how effectively an AI can learn about a person's likes and dislikes, making informed decisions while swiping on Tinder.

## Features

- [x] Swiping right on Tinder
- [x] Swiping left on Tinder
- [ ] Messaging on Tinder
- [ ] Matching on Tinder
- [ ] Super liking on Tinder
- [ ] Auto-login

## Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/SantaCRC/Tinder-IA.git
2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
3. **Run the bot:**
   ```sh
   python main.py
If it is your first time running the bot, it will create a .env file. Add your token auth information in this file, then run the bot again. (In future versions, the auth will be done automatically.)

4. **Add your Tinder account:**
   - Open Tinder in your browser.
   - Log in to your account.
   - Copy the token from the network tab in the developer tools.
   - Paste the token in the .env file.

## Usage
The first time you run the bot, if no model is found, it will start training a new model. This process can take a few minutes, depending on your hardware. After the model is trained, the bot will start swiping on Tinder.
