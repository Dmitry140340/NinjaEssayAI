# GymMindAIbot

This project is a Python-based Telegram bot with subscription payment and Coze API integration.

## Features
- Handles subscription payments using Telegram Payment API.
- Integrates with Coze API to provide AI-powered responses.
- Securely manages user interactions and payments.

## Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd GymMindAIbot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file in the project root and add the following:
   ```env
   TELEGRAM_BOT_TOKEN=<your-telegram-bot-token>
   COZE_API_URL=<your-coze-api-url>
   COZE_API_KEY=<your-coze-api-key>
   PAYMENT_PROVIDER_TOKEN=<your-payment-provider-token>
   ```

4. **Run the bot:**
   ```bash
   python bot.py
   ```

## Notes
- Replace placeholders in the `.env` file with your actual credentials.
- Ensure that your Telegram bot is configured to accept payments through a supported provider.

## License
This project is licensed under the MIT License.