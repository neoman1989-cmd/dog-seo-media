const {test,expect} = require('@playwright/test');
const path=require('path');
const pages=[['home','/','離れている時間も'],['comparison','/?name=camera-comparison','犬の留守番用ペットカメラの比較'],['policy','/?pagename=editorial-policy','編集方針・運営者情報']];
for(const [name,url,heading] of pages){
 test(name,async({page},info)=>{
  const errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  const response=await page.goto(url);
  expect(response.status()).toBe(200);
  await expect(page.locator('main h1')).toContainText(heading);
  await expect(page.locator('header nav')).toBeVisible();
  await expect(page.locator('footer')).toBeVisible();
  expect(await page.locator('nav ul').evaluate(el=>getComputedStyle(el).listStyleType)).toBe('none');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  if(name==='home'){
   await expect(page.locator('#latest article')).toHaveCount(1);
   expect((await page.locator('#latest article p').innerText()).length).toBeLessThanOrEqual(111);
   await page.locator('#latest article a').click();
   await expect(page.locator('main h1')).toContainText('比較');
   await page.goto(url);
  }
  if(name==='comparison'){
   await expect(page.locator('table')).toBeVisible();
   const region=page.getByRole('region',{name:'比較表（横にスクロールできます）'});
   await region.focus();
   await expect(region).toBeFocused();
   if(info.project.name.startsWith('mobile')){
    await page.keyboard.press('ArrowRight');
    await page.waitForTimeout(300);
    expect(await region.evaluate(el=>el.scrollLeft)).toBeGreaterThan(0);
    await region.evaluate(el=>el.scrollLeft=0);
   }
   await expect(page.locator('table caption')).toContainText('比較');
   await expect(page.locator('.notice')).toContainText('広告');
   const metrics=await page.locator('table').evaluate(el=>({width:el.offsetWidth,parentWidth:el.parentElement.clientWidth,overflow:getComputedStyle(el.parentElement).overflowX}));
   if(info.project.name.startsWith('mobile')){
    expect(metrics.width).toBeGreaterThan(metrics.parentWidth);
    expect(['auto','scroll']).toContain(metrics.overflow);
   }
  }
  expect(errors).toEqual([]);
  await page.screenshot({path:path.resolve(__dirname,'../../artifacts/wordpress',`${info.project.name}-${name}.png`),fullPage:true});
 });
}
