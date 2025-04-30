import Keyboard from 'https://cdn.jsdelivr.net/npm/simple-keyboard@3.7.1/build/index.js';

export function attachVirtualKeyboard(inputSelector='input'){
  const keyboard = new Keyboard({
    onChange: input => document.activeElement.value = input,
    onKeyPress: key => {
      if(key==="{enter}") document.activeElement.form?.dispatchEvent(new Event('submit'));
    }
  });
  document.querySelectorAll(inputSelector).forEach(inp=>{
    inp.setAttribute('inputmode','none');
    inp.addEventListener('focus',()=>keyboard.setInput(inp.value));
  })
}
