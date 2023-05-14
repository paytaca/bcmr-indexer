const ENCODED_URL = process.argv[2]

const PREPEND_HEX = ENCODED_URL.substring(0,2)
const URL_HEX = ENCODED_URL.substring(2)


const getPrepend = (utf8Bytes) => {
  let prepend = utf8Bytes.length.toString(16)
  prepend = prepend.length === 1 ? `0${prepend}` : prepend
  return prepend
}
const fromHexString = (hexString) =>
  Uint8Array.from(hexString.match(/.{1,2}/g).map((byte) => parseInt(byte, 16)))

// fetch https url without the `https://`

const bytes = fromHexString(URL_HEX)
const result = {
  success: false,
  url: null
}

// validate if prepend hex is same with actual hex of bytes length
if (getPrepend(bytes) === PREPEND_HEX) {
  result.success = true
  result.url = new TextDecoder().decode(bytes)
}

console.log(JSON.stringify(result))
