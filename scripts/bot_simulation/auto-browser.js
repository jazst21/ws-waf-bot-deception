const puppeteer = require('puppeteer');

async function main() {

  try {
    // init browser
    const browser = await puppeteer.launch({
      headless: false // false for show browser
    });

    // create page
    const page = await browser.newPage();


    for(i=0;i<3;i++){
        console.log('try:',i);

        // go to URL
        await page.goto('https://d2gy6opttm3z3x.cloudfront.net');

    }

    // uncomment to close browser
     //await browser.close();

  } catch (error) {
    console.error('error running:', error);
  }
}

main();
