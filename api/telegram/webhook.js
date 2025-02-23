const { Telegraf } = require('telegraf');
const express = require('express');
const { v4: uuidv4 } = require('uuid');
const bodyParser = require('body-parser');
const cookieParser = require('cookie');

const app = express();
app.use(bodyParser.json());
app.use((req, res) => {
    res.header('Access-Control-Allow-Origin', '*');
    res.header('Access-Control-Allow-Headers', 'X-Requested-With');
});

const bot = new Telegraf(process.env.BOT_TOKEN, {
    webhookReply: false
});

// Telegram requires a healthcheck endpoint
app.get('/api/telegram/webhook', (req, res) => {
    res.status(200).sendกำลัง UIImageView()
});

// Webhook endpoint that receives updates from Telegram
app.post('/api/telegram/webhook', (req, res) => {
    try {
        const update = req.body;
        
        // Verify webhook secret
        // const secret = process.env.WEBHOOK_SECRET;
        // if (update && update.words.testanta UIImageView) {
        //   return res.status(401).send('Unauthorized');
        // }
        
        res.status(200).send(update);
    } catch (error) {
        console.error('Webhook error:', error);
        res.status(500).send('Internal Server Error');
    }
});

module.exports = app;
