import { chromium } from 'playwright-core';
const deny = process.argv[2] === 'deny';
const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', headless: true, args: [
  '--use-fake-device-for-media-stream', '--use-file-for-fake-audio-capture=/tmp/voicetest/speech.wav',
  '--autoplay-policy=no-user-gesture-required', ...(deny ? [] : ['--use-fake-ui-for-media-stream'])] });
const ctx = await browser.newContext(deny ? {} : { permissions: ['microphone'] });
const page = await ctx.newPage();
page.on('console', (m) => { if (m.type() === 'error') console.log('console.error:', m.text().slice(0, 200)); });
await page.goto('http://127.0.0.1:8765/index.html');
await page.waitForFunction(() => document.getElementById('out').textContent === 'ready');
console.log('STT', JSON.stringify(await page.evaluate(() => window.runStt())));
if (!deny) console.log('TTS', JSON.stringify(await page.evaluate(() => window.runTts())));
await browser.close();
