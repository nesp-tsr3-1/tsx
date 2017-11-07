import _ from 'underscore'

// Converts a simple query string a=b&c=d&e=f into a javascript object
// Doesn't allow for keys with more than one - last value overwrites previous values for a given key
export function parseParams(queryString) {
  var params = {}
  var regex = /([^&=]+)=([^&]*)/g
  var m

  while(true) {
    m = regex.exec(queryString)
    if(!m) break
    params[decodeURIComponent(m[1])] = decodeURIComponent(m[2])
  }
  return params
}

export function encodeParams(params) {
  return _.chain(params)
    .pairs()
    .map(function(p) {
      return encodeURIComponent(p[0]) + '=' + encodeURIComponent(p[1])
    })
    .sort()
    .value()
    .join('&')
}

// Prompts user to select a file
// returns a promise that resolves to the selected file(s)
// options: accept, multiple
export function selectFiles(options) {
  options = options || {}
  return new Promise(function(resolve, reject) {
    var input = document.createElement('input')
    input.setAttribute('style', 'display: none')
    input.setAttribute('type', 'file')
    if(options.accept) {
      input.setAttribute('accept', options.accept)
    }
    if(options.multiple) {
      input.setAttribute('multiple', '')
    }
    document.body.appendChild(input)

    input.addEventListener('change', function() {
      resolve(input.files)
      document.body.removeChild(input)
    })
    input.click()
  })
}
