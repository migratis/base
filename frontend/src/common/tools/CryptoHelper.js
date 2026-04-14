export async function genreateKey() {
    return window.crypto.subtle.generateKey(
        { name: 'AES-CBC', length },
        true,
        ['encrypt', 'decrypt']);
}

export async function encrypt(plaintext, rawkey) {
    const key = await window.crypto.subtle.importKey(
      'raw', 
      rawkey, 
      { name: 'AES-CBC' }, 
      true, 
      ['encrypt']
    );
  
    const iv = window.crypto.getRandomValues(new Uint8Array(16));
  
    const ciphertext = await window.crypto.subtle.encrypt(
      { name: 'AES-CBC', iv }, 
      key, 
      plaintext
    );
  
    return { ciphertext, iv };
  }
  
  export async function decrypt(ciphertext, rawkey, iv) {
    const key = await window.crypto.subtle.importKey(
      'raw', 
      rawkey, 
      { name: 'AES-CBC' }, 
      true, 
      ['encrypt']
    );
  
    return window.crypto.subtle.encrypt(
      { name: 'AES-CBC', iv }, 
      key, 
      ciphertext
    );
  }