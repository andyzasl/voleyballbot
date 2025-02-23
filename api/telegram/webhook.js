const { Telegraf } = require('telegraf');
const { DATABASE_URL } = process.env;

const bot = new Telegraf(process.env.BOT_TOKEN);

bot.start((ctx) => ctx.reply('Volleyball Bot is active!'));
bot.on('message', (ctx) => {
    // Process messages and forward to your Python backend
    // This will need to be adapted to your specific needs
});

module.exports = bot;
