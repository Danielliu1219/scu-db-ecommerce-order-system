import headphones from '../assets/products/headphones.jpg'
import mouse from '../assets/products/mouse.jpg'
import notebook from '../assets/products/notebook.jpg'
import pen from '../assets/products/pen.jpg'
import mug from '../assets/products/mug.jpg'
import bottle from '../assets/products/bottle.jpg'
import lamp from '../assets/products/lamp.jpg'

// Original UI implementation. Visual direction: guizang-ppt-skill Swiss / IKB.
// Product photographs: Unsplash, licensed at https://unsplash.com/license.
export function productArt(name: string): string | undefined {
  if (/耳机/.test(name)) return headphones
  if (/鼠标/.test(name)) return mouse
  if (/笔记本|本子/.test(name)) return notebook
  if (/笔/.test(name)) return pen
  if (/保温|随行/.test(name)) return bottle
  if (/杯/.test(name)) return mug
  if (/灯/.test(name)) return lamp
}
export const editorialImage = notebook
