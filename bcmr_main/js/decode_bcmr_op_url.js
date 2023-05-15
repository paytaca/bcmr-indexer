const ENCODED_URL = process.argv[2]


const fromHexString = (hexString) =>
  Uint8Array.from(hexString.match(/.{1,2}/g).map((byte) => parseInt(byte, 16)))

const bytes = fromHexString(ENCODED_URL)
const decodedUrl = new TextDecoder().decode(bytes)
console.log(decodedUrl)


// NOTE: to check BCMR tag's first hex value if it matches the length of the binary format of "BCMR"
// const getPrepend = (utf8Bytes) => {
//   let prepend = utf8Bytes.length.toString(16)
//   prepend = prepend.length === 1 ? `0${prepend}` : prepend
//   return prepend
// }

// // ENCODE
// const encoder = new TextEncoder('utf-8')
// const uint8arr = encoder.encode('gist.githubusercontent.com/joemarct/06a218f5daf0160a93a4d0a8a43375d3/raw')
// const hex = Buffer.from(uint8arr).toString('hex');
// console.log(hex)

// // DECODE
// const fromHexString = (hexString) =>
//   Uint8Array.from(hexString.match(/.{1,2}/g).map((byte) => parseInt(byte, 16)))

// const bytes = fromHexString('676973742e67697468756275736572636f6e74656e742e636f6d2f6a6f656d617263742f30366132313866356461663031363061393361346430613861343333373564332f726177')
// const decoded = new TextDecoder().decode(bytes)
// console.log(decoded)
