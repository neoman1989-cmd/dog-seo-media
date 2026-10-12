const {test,expect}=require('@playwright/test');
const fs=require('fs'),path=require('path');
const records=JSON.parse(fs.readFileSync(path.resolve(__dirname,'../../artifacts/phase3/wp-posts.json'),'utf8'));
const credentials=fs.readFileSync(path.resolve(__dirname,'../.env'),'utf8');
const password=credentials.split('\n').find(line=>line.startsWith('LOCAL_WP_PASSWORD=')).slice('LOCAL_WP_PASSWORD='.length);
for(const slug of ['camera-selection','camera-monthly-cost','camera-recording']){
 test(slug,async({page,browser},info)=>{
  const record=records.find(post=>post.post_name===slug);
  expect(record.post_status).toBe('draft');
  // Anonymous visitors must not be able to read the draft.
  const anonymous=await browser.newContext(); const outsider=await anonymous.newPage();
  const publicResponse=await outsider.goto('/?p='+record.ID);
  expect(publicResponse.status()).toBe(404);await anonymous.close();
  await page.goto('/wp-login.php');
  await page.locator('#user_login').fill('local-editor');
  await page.locator('#user_pass').fill(password);
  await page.locator('#wp-submit').click();
  await page.waitForURL('**/wp-admin/**');
  const response=await page.goto('/?p='+record.ID+'&preview=true');
  expect(response.status()).toBe(200);
  await expect(page.locator('main h1')).toBeVisible();
  await expect(page.locator('main')).toContainText('公式資料の引用に基づく編集下書き');
  await expect(page.locator('main')).toContainText('未確認');
  await expect(page.locator('table tbody tr')).toHaveCount(5);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  const sourceLinks=page.locator('main table a');
  for(const link of await sourceLinks.all()) expect(await link.getAttribute('href')).toMatch(/^https:\/\/www\.tp-link\.com\//);
  await page.screenshot({path:path.resolve(__dirname,'../../artifacts/phase3',`${info.project.name}-${slug}.png`),fullPage:true});
 });
}
